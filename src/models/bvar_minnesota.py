"""
BVAR com Prior Minnesota para Spillovers FED-Selic
Implementação para cenários condicionais com amostras pequenas

Melhorias técnicas (v2.0):
- Prior Minnesota escalado por variância empírica
- Estabilização numérica com ridge e PSD enforcement
- IRFs estruturais com identificação Cholesky (Fed→Selic)
- Previsão condicional dinâmica recursiva

Baseado em:
- Litterman, R. B. (1986): "Forecasting with Bayesian Vector Autoregressions"
- Doan, T., Litterman, R., & Sims, C. (1984): "Forecasting and Conditional Projection"
- Banbura, M., Giannone, D., & Reichlin, L. (2010): "Large Bayesian Vector Autoregressions"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
from scipy.linalg import solve, cholesky
import warnings
warnings.filterwarnings('ignore')

class BVARMinnesota:
    """
    BVAR com Prior Minnesota para spillovers FED-Selic
    
    Implementa:
    - Prior Minnesota escalado por variância empírica
    - Previsões condicionais dinâmicas para cenários específicos
    - IRFs estruturais com identificação Cholesky
    - Estabilização numérica para amostras pequenas
    - Simulação de distribuições preditivas
    """
    
    def __init__(self, 
                 n_lags: int = 2,
                 n_vars: int = 2,  # Fed e Selic
                 minnesota_params: Dict[str, float] = None,
                 n_simulations: int = 1000,
                 random_state: int = 42):
        """
        Inicializar BVAR com Prior Minnesota
        
        Args:
            n_lags: Número de lags do VAR
            n_vars: Número de variáveis (Fed, Selic)
            minnesota_params: Parâmetros do prior Minnesota
                - lambda1: Shrinkage geral (recomendado: 0.2-0.3)
                - lambda2: Cross-equation shrinkage (recomendado: 0.5)
                - lambda3: Decaimento de lags (recomendado: 1.0)
                - lambda4: Shrinkage de covariância (não usado em v2.0)
                - mu: Prior mean para intercepto
                - sigma: Prior std para intercepto
            n_simulations: Número de simulações para distribuições preditivas
            random_state: Seed para reprodutibilidade
        """
        self.n_lags = n_lags
        self.n_vars = n_vars
        self.n_simulations = n_simulations
        self.random_state = random_state
        
        # Configurar random state
        np.random.seed(random_state)
        
        # Parâmetros do Prior Minnesota (ajustados para N pequeno)
        if minnesota_params is None:
            self.minnesota_params = {
                'lambda1': 0.2,    # Shrinkage geral (conservador para N pequeno)
                'lambda2': 0.5,    # Cross-equation shrinkage
                'lambda3': 1.0,    # Decaimento de lags
                'mu': 0.0,         # Prior mean para intercepto
                'sigma': 10.0      # Prior std para intercepto (relaxado)
            }
        else:
            self.minnesota_params = minnesota_params
        
        # Matrizes do modelo
        self.Y = None  # Dados endógenos
        self.X = None  # Regressores (lags + constante)
        self.beta = None  # Coeficientes estimados
        self.sigma = None  # Matriz de covariância dos resíduos
        self.prior_mean = None  # Prior mean dos coeficientes
        self.prior_var = None  # Prior variance dos coeficientes
        
        # Resultados
        self.irfs = {}
        self.forecasts = {}
        
    def prepare_data(self, 
                    fed_data: pd.Series, 
                    selic_data: pd.Series,
                    fed_dates: pd.DatetimeIndex,
                    selic_dates: pd.DatetimeIndex) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preparar dados para BVAR
        
        Args:
            fed_data: Série de movimentos do Fed (bps)
            selic_data: Série de movimentos da Selic (bps)
            fed_dates: Datas das decisões do Fed
            selic_dates: Datas das decisões do Copom
            
        Returns:
            Matrizes Y (endógenas) e X (regressores)
        """
        print("🔧 Preparando dados para BVAR Minnesota...")
        
        # Alinhar séries temporais
        min_date = max(fed_dates.min(), selic_dates.min())
        max_date = min(fed_dates.max(), selic_dates.max())
        
        # Criar índice mensal
        date_range = pd.date_range(start=min_date, end=max_date, freq='M')
        
        # Interpolar dados para frequência mensal
        # Nota: forward-fill é uma aproximação; idealmente usar reuniões diretamente
        fed_monthly = self._interpolate_to_monthly(fed_data, fed_dates, date_range)
        selic_monthly = self._interpolate_to_monthly(selic_data, selic_dates, date_range)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'fed_move': fed_monthly,
            'selic_move': selic_monthly,
            'date': date_range
        }).dropna()
        
        # Criar matrizes Y e X
        X = self._create_lag_matrix(df[['fed_move', 'selic_move']], self.n_lags)
        
        # Y deve ter o mesmo número de linhas que X (remover primeiros n_lags)
        Y = df[['fed_move', 'selic_move']].values[self.n_lags:, :]
        
        # Adicionar constante
        X = np.column_stack([np.ones(X.shape[0]), X])
        
        # Verificar alinhamento
        assert Y.shape[0] == X.shape[0], f"Dimensões incompatíveis: Y={Y.shape}, X={X.shape}"
        
        self.Y = Y
        self.X = X
        
        print(f"✅ Dados preparados: {Y.shape[0]} observações, {Y.shape[1]} variáveis")
        print(f"   ⚠️  Nota: Dados mensalizados por forward-fill (simplificação MVP)")
        return Y, X
    
    def _interpolate_to_monthly(self, 
                               data: pd.Series, 
                               dates: pd.DatetimeIndex, 
                               target_dates: pd.DatetimeIndex) -> pd.Series:
        """Interpolar dados para frequência mensal"""
        ts = pd.Series(data.values, index=dates)
        ts_monthly = ts.reindex(target_dates, method='ffill')
        return ts_monthly
    
    def _create_lag_matrix(self, df: pd.DataFrame, n_lags: int) -> np.ndarray:
        """Criar matriz de lags para VAR"""
        n_obs = len(df)
        n_vars = df.shape[1]
        
        # Inicializar matriz de lags
        lag_matrix = np.zeros((n_obs - n_lags, n_vars * n_lags))
        
        for lag in range(1, n_lags + 1):
            start_idx = (lag - 1) * n_vars
            end_idx = lag * n_vars
            lag_matrix[:, start_idx:end_idx] = df.iloc[n_lags - lag:n_obs - lag].values
        
        return lag_matrix
    
    def _create_minnesota_prior(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Criar Prior Minnesota escalado por variância empírica
        
        Prior: β ~ N(μ_prior, V_prior)
        
        Variância prior para coeficiente da variável j na equação i no lag ℓ:
        - Own lag (j=i): (λ1^2 / ℓ^λ3) * (σ_i^2 / σ_j^2)
        - Cross lag (j≠i): λ2^2 * (λ1^2 / ℓ^λ3) * (σ_i^2 / σ_j^2)
        """
        n_coefs = self.n_vars * self.n_lags + 1  # +1 para intercepto
        n_params = self.n_vars * n_coefs
        
        # Estimar variância empírica das séries (diferenças)
        if self.Y.shape[0] > 1:
            diffs = np.diff(self.Y, axis=0)
        else:
            diffs = self.Y
        
        var_i = np.var(diffs, axis=0, ddof=1) + 1e-6  # evitar divisão por zero
        
        # Prior mean (todos zeros exceto intercepto)
        prior_mean = np.zeros(n_params)
        for i in range(self.n_vars):
            prior_mean[i * n_coefs] = self.minnesota_params['mu']
        
        # Extrair hiperparâmetros
        lam1 = self.minnesota_params['lambda1']
        lam2 = self.minnesota_params['lambda2']
        lam3 = self.minnesota_params['lambda3']
        sig0 = self.minnesota_params['sigma']
        
        # Prior variance (matriz diagonal)
        prior_var = np.zeros((n_params, n_params))
        
        for i in range(self.n_vars):
            # Intercepto
            idx_int = i * n_coefs
            prior_var[idx_int, idx_int] = sig0 ** 2
            
            # Lags
            for ell in range(1, self.n_lags + 1):
                for j in range(self.n_vars):
                    idx = i * n_coefs + 1 + (ell - 1) * self.n_vars + j
                    
                    # Base variance (decai com lag)
                    base = (lam1 ** 2) / (ell ** lam3)
                    
                    # Escalar por variância das séries
                    scale = (var_i[i] / var_i[j]) if var_i[j] > 0 else 1.0
                    
                    # Cross-equation shrinkage
                    cross = (lam2 ** 2) if j != i else 1.0
                    
                    prior_var[idx, idx] = base * scale * cross
        
        return prior_mean, prior_var
    
    def estimate(self) -> Dict[str, any]:
        """
        Estimar BVAR com Prior Minnesota
        
        Posterior: β | Y, X ~ N(μ_post, V_post)
        onde:
        - V_post = (V_prior^{-1} + X'X + εI)^{-1}  (com ridge para estabilidade)
        - μ_post = V_post * (V_prior^{-1} * μ_prior + X'Y)
        
        Melhorias v2.0:
        - Ridge mínimo para estabilidade numérica
        - Sigma PSD enforcement
        """
        print("🔬 Estimando BVAR com Prior Minnesota...")
        
        if self.Y is None or self.X is None:
            raise ValueError("Dados não preparados. Execute prepare_data() primeiro.")
        
        # Criar prior Minnesota escalado
        prior_mean, prior_var = self._create_minnesota_prior()
        
        # Preparar dados para estimação
        Y_vec = self.Y.flatten()
        X_kron = np.kron(np.eye(self.n_vars), self.X)
        
        # Ridge mínimo para estabilidade com N pequeno
        eps = 1e-8
        
        # Calcular posterior com pseudoinverse para estabilidade
        prior_var_inv = np.linalg.pinv(prior_var)
        XtX = X_kron.T @ X_kron
        posterior_var = np.linalg.pinv(prior_var_inv + XtX + eps * np.eye(X_kron.shape[1]))
        posterior_mean = posterior_var @ (prior_var_inv @ prior_mean + X_kron.T @ Y_vec)
        
        # Reshape para matriz de coeficientes
        self.beta = posterior_mean.reshape(self.n_vars, -1)
        
        # Calcular matriz de covariância dos resíduos com PSD enforcement
        Y_pred = X_kron @ posterior_mean
        residuals = (Y_vec - Y_pred).reshape(self.Y.shape)
        
        # Sigma com garantia de PSD (nearest positive semi-definite)
        sigma = np.cov(residuals.T)
        sigma = 0.5 * (sigma + sigma.T)  # forçar simetria
        
        # Eigenvalue correction para PSD
        eigvals, eigvecs = np.linalg.eigh(sigma)
        eigvals[eigvals < 1e-8] = 1e-8
        self.sigma = (eigvecs @ np.diag(eigvals) @ eigvecs.T)
        
        # Armazenar prior
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        
        # Calcular IRFs estruturais
        self._calculate_irfs_structural()
        
        results = {
            'beta': self.beta,
            'sigma': self.sigma,
            'prior_mean': prior_mean,
            'prior_var': prior_var,
            'posterior_mean': posterior_mean,
            'posterior_var': posterior_var,
            'n_obs': self.Y.shape[0],
            'n_vars': self.n_vars,
            'n_lags': self.n_lags,
            'random_state': self.random_state
        }
        
        print(f"✅ BVAR estimado: {self.n_vars} variáveis, {self.n_lags} lags")
        print(f"   Sigma eigenvalues: {eigvals}")
        return results
    
    def _calculate_irfs_structural(self, max_horizon: int = 12):
        """
        Calcular IRFs estruturais com identificação Cholesky
        
        Ordenação: Fed → Selic (Fed é contemporaneamente exógeno)
        
        Melhorias v2.0:
        - Forma companion para cálculo eficiente
        - Identificação estrutural via Cholesky
        - Choques ortogonais
        """
        print("📊 Calculando IRFs estruturais (Cholesky: Fed→Selic)...")
        
        # Extrair matrizes A1..Ap (sem intercepto)
        k = self.n_vars
        p = self.n_lags
        A = []
        for lag in range(1, p + 1):
            start = 1 + (lag - 1) * k
            A.append(self.beta[:, start:start + k])
        
        # Montar forma companion
        F = np.zeros((k * p, k * p))
        F[:k, :k * p] = np.hstack(A)
        if p > 1:
            F[k:, :k * (p - 1)] = np.eye(k * (p - 1))
        
        # Identificação estrutural via Cholesky
        # Ordenação: Fed (0) → Selic (1)
        try:
            L = np.linalg.cholesky(self.sigma + 1e-8 * np.eye(k))
        except np.linalg.LinAlgError:
            print("⚠️  Cholesky falhou, usando aproximação")
            eigvals, eigvecs = np.linalg.eigh(self.sigma)
            eigvals[eigvals < 1e-8] = 1e-8
            sigma_psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
            L = np.linalg.cholesky(sigma_psd)
        
        # Calcular IRFs estruturais
        irf = np.zeros((max_horizon + 1, k, k))
        irf[0] = L  # Impacto contemporâneo
        
        Fpow = np.eye(k * p)
        for h in range(1, max_horizon + 1):
            Fpow = Fpow @ F
            irf[h] = (Fpow[:k, :k]) @ L
        
        # Armazenar IRFs
        self.irfs = {f'h_{h}': irf[h] for h in range(max_horizon + 1)}
        
        print(f"✅ IRFs estruturais calculados (horizonte 0-{max_horizon})")
    
    def conditional_forecast(self, 
                           fed_path: List[float],
                           horizon_months: int = 12,
                           n_simulations: int = None) -> Dict[str, any]:
        """
        Previsão condicional dinâmica com simulação recursiva
        
        Implementa cenário impondo caminho do Fed e propagando Selic endógena.
        
        Melhorias v2.0:
        - Simulação recursiva (não apenas IRF*shock)
        - Estado inicial dos últimos p lags observados
        - Fed imposto exogenamente, Selic evolui endógena + ruído
        
        Args:
            fed_path: Caminho futuro do Fed (bps por período)
            horizon_months: Horizonte de previsão
            n_simulations: Número de simulações
            
        Returns:
            Distribuições preditivas condicionais por horizonte
        """
        if n_simulations is None:
            n_simulations = self.n_simulations
        
        # Reset random state para reprodutibilidade
        np.random.seed(self.random_state)
        
        print(f"🔮 Previsão condicional dinâmica para {len(fed_path)} períodos...")
        
        k, p = self.n_vars, self.n_lags
        
        # Extrair coeficientes A1..Ap e intercepto c
        A = [self.beta[:, 1 + i * k: 1 + (i + 1) * k] for i in range(p)]
        c = self.beta[:, 0]
        
        # Estado inicial: últimos p observados da amostra
        Yhist = self.Y[-p:, :].copy() if self.Y.shape[0] >= p else np.zeros((p, k))
        
        forecasts = {}
        
        for h in range(1, min(horizon_months, len(fed_path)) + 1):
            selic_draws = np.zeros(n_simulations)
            
            for s in range(n_simulations):
                # Estado para esta simulação
                y_stack = Yhist.copy()
                
                # Construir previsão do próximo passo
                y_next = c.copy()
                
                # Fed imposto exogenamente
                fed_imposed = fed_path[h - 1] if h - 1 < len(fed_path) else fed_path[-1] if fed_path else 0.0
                
                # Contribuição dos lags
                for ell in range(1, p + 1):
                    y_next += A[ell - 1] @ y_stack[-ell, :]
                
                # Impor Fed (substituir componente Fed na forma reduzida)
                y_next[0] = fed_imposed
                
                # Adicionar ruído estrutural
                shock = np.random.multivariate_normal(mean=np.zeros(k), cov=self.sigma)
                y_next = y_next + shock
                
                # Coletar Selic desta simulação
                selic_draws[s] = y_next[1]
                
                # Atualizar histórico para próximo passo (usar média para continuidade)
                if s == 0:  # Só atualiza uma vez por horizonte
                    Yhist = np.vstack([Yhist, [fed_imposed, np.mean(selic_draws[:max(1, s)])]])[-p:, :]
            
            # Estatísticas da distribuição para este horizonte
            forecasts[f'h_{h}'] = {
                'mean': float(np.mean(selic_draws)),
                'std': float(np.std(selic_draws, ddof=1)),
                'ci_lower': float(np.percentile(selic_draws, 2.5)),
                'ci_upper': float(np.percentile(selic_draws, 97.5)),
                'ci_80_lower': float(np.percentile(selic_draws, 10)),
                'ci_80_upper': float(np.percentile(selic_draws, 90)),
                'fed_imposed': float(fed_imposed),
                'n_simulations': n_simulations
            }
            
            print(f"  h={h}: Selic {forecasts[f'h_{h}']['mean']:.1f} bps "
                  f"[{forecasts[f'h_{h}']['ci_lower']:.1f}, {forecasts[f'h_{h}']['ci_upper']:.1f}] "
                  f"dado Fed={fed_imposed:.1f} bps")
        
        self.forecasts = forecasts
        return forecasts
    
    def scenario_analysis(self, 
                         scenarios: Dict[str, List[float]]) -> Dict[str, Dict[str, any]]:
        """
        Análise de cenários múltiplos
        
        Args:
            scenarios: Dicionário com cenários {nome: caminho_fed}
            
        Returns:
            Resultados por cenário
        """
        print(f"📊 Análise de {len(scenarios)} cenários...")
        
        results = {}
        
        for scenario_name, fed_path in scenarios.items():
            print(f"  🔍 Cenário: {scenario_name}")
            
            # Previsão condicional
            forecast = self.conditional_forecast(fed_path)
            
            # Resumir resultados
            summary = {
                'scenario_name': scenario_name,
                'fed_path': fed_path,
                'forecasts': forecast,
                'avg_selic_response': np.mean([f['mean'] for f in forecast.values()]),
                'max_selic_response': np.max([f['mean'] for f in forecast.values()]),
                'horizon_max_response': max(forecast.keys(), key=lambda k: forecast[k]['mean'])
            }
            
            results[scenario_name] = summary
        
        return results
    
    def get_irf_summary(self) -> Dict[str, any]:
        """
        Resumo das IRFs estruturais
        
        IRF[h, 1, 0] = resposta da Selic (var 1) a choque estrutural do Fed (var 0)
        """
        if not self.irfs:
            return {}
        
        summary = {
            'max_response': 0.0,
            'horizon_max_response': 0,
            'persistence': 0.0,
            'irf_values': {},
            'method': 'structural_cholesky'
        }
        
        max_response = 0
        horizon_max = 0
        
        for horizon, irf_matrix in self.irfs.items():
            # Resposta da Selic (1) ao choque estrutural do Fed (0)
            selic_response = abs(irf_matrix[1, 0])
            summary['irf_values'][horizon] = selic_response
            
            if selic_response > max_response:
                max_response = selic_response
                horizon_max = int(horizon.split('_')[1])
        
        summary['max_response'] = max_response
        summary['horizon_max_response'] = horizon_max
        
        # Calcular persistência (soma das respostas)
        summary['persistence'] = sum(summary['irf_values'].values())
        
        return summary
    
    def evaluate_model(self) -> Dict[str, any]:
        """Avaliar qualidade do modelo"""
        if self.beta is None:
            return {'error': 'Modelo não estimado'}
        
        # Calcular R²
        Y_pred = self.X @ self.beta.T
        ss_res = np.sum((self.Y - Y_pred) ** 2)
        ss_tot = np.sum((self.Y - np.mean(self.Y, axis=0)) ** 2)
        r_squared = 1 - ss_res / ss_tot
        
        # Resumo das IRFs
        irf_summary = self.get_irf_summary()
        
        evaluation = {
            'r_squared': r_squared,
            'n_obs': self.Y.shape[0],
            'n_vars': self.n_vars,
            'n_lags': self.n_lags,
            'irf_summary': irf_summary,
            'prior_strength': float(np.trace(self.prior_var) / (np.trace(np.linalg.pinv(self.prior_var)) + 1e-8)),
            'model_quality': 'good' if np.mean(r_squared) > 0.3 else 'moderate' if np.mean(r_squared) > 0.1 else 'weak',
            'sigma_condition_number': float(np.linalg.cond(self.sigma)),
            'identification': 'cholesky_fed_first'
        }
        
        return evaluation


if __name__ == "__main__":
    # Teste do BVAR Minnesota v2.0
    print("🧪 Testando BVAR Minnesota v2.0 (melhorias técnicas)...")
    
    # Dados sintéticos para teste
    np.random.seed(42)
    n = 50
    
    # Gerar séries com spillover Fed→Selic
    fed_moves = np.random.normal(0, 25, n)
    selic_moves = 0.3 * fed_moves + np.random.normal(0, 15, n)
    
    # Criar datas
    dates = pd.date_range('2020-01-01', periods=n, freq='M')
    
    # Criar BVAR v2.0
    bvar = BVARMinnesota(
        n_lags=2, 
        n_vars=2,
        minnesota_params={
            'lambda1': 0.2,
            'lambda2': 0.5,
            'lambda3': 1.0,
            'mu': 0.0,
            'sigma': 10.0
        },
        n_simulations=1000,
        random_state=42
    )
    
    # Preparar dados
    Y, X = bvar.prepare_data(
        fed_data=pd.Series(fed_moves),
        selic_data=pd.Series(selic_moves),
        fed_dates=dates,
        selic_dates=dates
    )
    
    # Estimar modelo
    results = bvar.estimate()
    
    # Avaliar modelo
    evaluation = bvar.evaluate_model()
    print(f"\n📊 Avaliação do BVAR v2.0:")
    print(f"  R² médio: {np.mean(evaluation['r_squared']):.3f}")
    print(f"  Observações: {evaluation['n_obs']}")
    print(f"  Qualidade: {evaluation['model_quality']}")
    print(f"  Condition number Sigma: {evaluation['sigma_condition_number']:.2f}")
    print(f"  Identificação: {evaluation['identification']}")
    
    # IRF summary
    irf_sum = evaluation['irf_summary']
    print(f"\n📈 IRFs Estruturais:")
    print(f"  Máxima resposta Selic→Fed: {irf_sum['max_response']:.3f}")
    print(f"  Horizonte de máxima: h={irf_sum['horizon_max_response']}")
    print(f"  Persistência total: {irf_sum['persistence']:.3f}")
    
    # Teste de previsão condicional dinâmica
    fed_scenario = [25, 0, -25, 0]  # Cenário: +25, 0, -25, 0
    forecast = bvar.conditional_forecast(fed_scenario, horizon_months=4)
    
    print(f"\n🔮 Previsão condicional dinâmica:")
    for horizon, pred in forecast.items():
        print(f"  {horizon}: Selic {pred['mean']:.1f} bps "
              f"[{pred['ci_lower']:.1f}, {pred['ci_upper']:.1f}] "
              f"dado Fed={pred['fed_imposed']:.1f}")
    
    # Análise de cenários
    scenarios = {
        'hawkish': [50, 25, 0, 0],
        'dovish': [-25, -25, 0, 0],
        'neutral': [0, 0, 0, 0]
    }
    
    scenario_results = bvar.scenario_analysis(scenarios)
    print(f"\n📊 Análise de cenários:")
    for scenario, result in scenario_results.items():
        print(f"  {scenario}: resposta média Selic {result['avg_selic_response']:.1f} bps")
    
    print("\n✅ Teste v2.0 concluído com sucesso!")
    print("🎯 Melhorias implementadas:")
    print("  ✓ Prior Minnesota escalado por variância")
    print("  ✓ Estabilização numérica (ridge + PSD)")
    print("  ✓ IRFs estruturais com Cholesky")
    print("  ✓ Previsão condicional dinâmica recursiva")
