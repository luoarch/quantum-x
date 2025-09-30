"""
BVAR com Prior Minnesota para Spillovers FED-Selic
Implementação para cenários condicionais com amostras pequenas

Melhorias técnicas (v2.1):
- Prior Minnesota escalado por variância empírica
- Estabilização numérica com ridge e PSD enforcement
- IRFs estruturais normalizados (1 bps Fed) com Cholesky
- Previsão condicional dinâmica recursiva consistente
- RNG local para reprodutibilidade
- Checagem de estabilidade (raízes AR)
- Serialização JSON para auditoria

Baseado em:
- Litterman, R. B. (1986): "Forecasting with Bayesian Vector Autoregressions"
- Doan, T., Litterman, R., & Sims, C. (1984): "Forecasting and Conditional Projection"
- Banbura, M., Giannone, D., & Reichlin, L. (2010): "Large Bayesian Vector Autoregressions"
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Literal
from scipy import stats
from scipy.linalg import solve, cholesky
import warnings

class BVARMinnesota:
    """
    BVAR com Prior Minnesota para spillovers FED-Selic
    
    v2.1 - Melhorias de robustez:
    - RNG local (não contamina global)
    - Estado multi-step consistente
    - Normalização de IRFs para 1 bps
    - Checagem de estabilidade
    - Serialização auditável
    """
    
    def __init__(self, 
                 n_lags: int = 2,
                 n_vars: int = 2,  # Fed e Selic
                 minnesota_params: Dict[str, float] = None,
                 n_simulations: int = 1000,
                 random_state: int = 42,
                 priors_profile: str = "small-N-default"):
        """
        Inicializar BVAR com Prior Minnesota
        
        Args:
            n_lags: Número de lags do VAR
            n_vars: Número de variáveis (Fed, Selic)
            minnesota_params: Parâmetros do prior Minnesota
                - lambda1: Shrinkage geral (0.2-0.3)
                - lambda2: Cross-equation shrinkage (0.3-0.5)
                - lambda3: Decaimento de lags (1.0-1.5)
                - mu: Prior mean para intercepto
                - sigma: Prior std para intercepto
            n_simulations: Número de simulações
            random_state: Seed para reprodutibilidade
            priors_profile: Perfil de priors ("small-N-default" ou custom)
        """
        self.n_lags = n_lags
        self.n_vars = n_vars
        self.n_simulations = n_simulations
        self.random_state = random_state
        self.priors_profile = priors_profile
        
        # RNG local para reprodutibilidade sem contaminar global
        self.rng = np.random.default_rng(random_state)
        
        # Priors ajustados para N pequeno
        if minnesota_params is None:
            self.minnesota_params = {
                'lambda1': 0.2,    # Shrinkage geral
                'lambda2': 0.4,    # Cross-equation (mais forte)
                'lambda3': 1.5,    # Decaimento lags > 1 (mais forte)
                'mu': 0.0,         # Prior mean intercepto
                'sigma': 10.0      # Prior std intercepto
            }
        else:
            self.minnesota_params = minnesota_params
        
        # Matrizes do modelo
        self.Y = None
        self.X = None
        self.beta = None
        self.sigma = None
        self.prior_mean = None
        self.prior_var = None
        
        # Metadados
        self.train_dates = None
        self.scale_info = None
        self.stable = None
        
        # Resultados
        self.irfs = {}
        self.forecasts = {}
        
    def prepare_data(self, 
                    fed_data: pd.Series, 
                    selic_data: pd.Series,
                    fed_dates: pd.DatetimeIndex,
                    selic_dates: pd.DatetimeIndex) -> Tuple[np.ndarray, np.ndarray]:
        """Preparar dados para BVAR"""
        print("🔧 Preparando dados para BVAR Minnesota v2.1...")
        
        # Alinhar séries temporais
        min_date = max(fed_dates.min(), selic_dates.min())
        max_date = min(fed_dates.max(), selic_dates.max())
        
        # Armazenar datas para metadata
        self.train_dates = {'start': str(min_date.date()), 'end': str(max_date.date())}
        
        # Criar índice mensal
        date_range = pd.date_range(start=min_date, end=max_date, freq='M')
        
        # Interpolar (forward-fill)
        fed_monthly = self._interpolate_to_monthly(fed_data, fed_dates, date_range)
        selic_monthly = self._interpolate_to_monthly(selic_data, selic_dates, date_range)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'fed_move': fed_monthly,
            'selic_move': selic_monthly,
            'date': date_range
        }).dropna()
        
        # Armazenar info de escala
        self.scale_info = {
            'fed_mean': float(df['fed_move'].mean()),
            'fed_std': float(df['fed_move'].std()),
            'selic_mean': float(df['selic_move'].mean()),
            'selic_std': float(df['selic_move'].std())
        }
        
        # Criar matrizes Y e X
        X = self._create_lag_matrix(df[['fed_move', 'selic_move']], self.n_lags)
        Y = df[['fed_move', 'selic_move']].values[self.n_lags:, :]
        X = np.column_stack([np.ones(X.shape[0]), X])
        
        # Validação crítica para N pequeno
        if Y.shape[0] < self.n_lags + 5:
            warnings.warn(
                f"⚠️  N muito pequeno! {Y.shape[0]} obs com {self.n_lags} lags. "
                f"Recomendado: N ≥ {self.n_lags + 10}. Bandas serão muito largas.",
                UserWarning
            )
        
        assert Y.shape[0] == X.shape[0], f"Dimensões incompatíveis: Y={Y.shape}, X={X.shape}"
        
        self.Y = Y
        self.X = X
        
        print(f"✅ Dados preparados: {Y.shape[0]} observações, {Y.shape[1]} variáveis")
        print(f"   ⚠️  Nota: Dados mensalizados por forward-fill (simplificação MVP)")
        return Y, X
    
    def _interpolate_to_monthly(self, data: pd.Series, dates: pd.DatetimeIndex, 
                               target_dates: pd.DatetimeIndex) -> pd.Series:
        """Interpolar dados para frequência mensal"""
        ts = pd.Series(data.values, index=dates)
        return ts.reindex(target_dates, method='ffill')
    
    def _create_lag_matrix(self, df: pd.DataFrame, n_lags: int) -> np.ndarray:
        """Criar matriz de lags para VAR"""
        n_obs = len(df)
        n_vars = df.shape[1]
        lag_matrix = np.zeros((n_obs - n_lags, n_vars * n_lags))
        
        for lag in range(1, n_lags + 1):
            start_idx = (lag - 1) * n_vars
            end_idx = lag * n_vars
            lag_matrix[:, start_idx:end_idx] = df.iloc[n_lags - lag:n_obs - lag].values
        
        return lag_matrix
    
    def _create_minnesota_prior(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prior Minnesota escalado por variância empírica
        
        v2.1: lambda3=1.5 para shrinkage extra em lags > 1
        """
        n_coefs = self.n_vars * self.n_lags + 1
        n_params = self.n_vars * n_coefs
        
        # Variância empírica
        diffs = np.diff(self.Y, axis=0) if self.Y.shape[0] > 1 else self.Y
        var_i = np.var(diffs, axis=0, ddof=1) + 1e-6
        
        # Prior mean
        prior_mean = np.zeros(n_params)
        for i in range(self.n_vars):
            prior_mean[i * n_coefs] = self.minnesota_params['mu']
        
        # Hiperparâmetros
        lam1 = self.minnesota_params['lambda1']
        lam2 = self.minnesota_params['lambda2']
        lam3 = self.minnesota_params['lambda3']
        sig0 = self.minnesota_params['sigma']
        
        # Prior variance
        prior_var = np.zeros((n_params, n_params))
        
        for i in range(self.n_vars):
            # Intercepto
            prior_var[i * n_coefs, i * n_coefs] = sig0 ** 2
            
            # Lags
            for ell in range(1, self.n_lags + 1):
                for j in range(self.n_vars):
                    idx = i * n_coefs + 1 + (ell - 1) * self.n_vars + j
                    base = (lam1 ** 2) / (ell ** lam3)
                    scale = (var_i[i] / var_i[j]) if var_i[j] > 0 else 1.0
                    cross = (lam2 ** 2) if j != i else 1.0
                    prior_var[idx, idx] = base * scale * cross
        
        return prior_mean, prior_var
    
    def estimate(self) -> Dict[str, any]:
        """
        Estimar BVAR com checagens de robustez
        
        v2.1: Adiciona ridge adaptativo e checagem de estabilidade
        """
        print("🔬 Estimando BVAR Minnesota v2.1...")
        
        if self.Y is None or self.X is None:
            raise ValueError("Dados não preparados. Execute prepare_data() primeiro.")
        
        # Prior escalado
        prior_mean, prior_var = self._create_minnesota_prior()
        
        # Preparar dados
        Y_vec = self.Y.flatten()
        X_kron = np.kron(np.eye(self.n_vars), self.X)
        
        # Ridge adaptativo
        eps = 1e-8
        prior_var_inv = np.linalg.pinv(prior_var)
        XtX = X_kron.T @ X_kron
        posterior_var = np.linalg.pinv(prior_var_inv + XtX + eps * np.eye(X_kron.shape[1]))
        posterior_mean = posterior_var @ (prior_var_inv @ prior_mean + X_kron.T @ Y_vec)
        
        # Coeficientes
        self.beta = posterior_mean.reshape(self.n_vars, -1)
        
        # Sigma com regularização adaptativa
        Y_pred = X_kron @ posterior_mean
        residuals = (Y_vec - Y_pred).reshape(self.Y.shape)
        sigma = np.cov(residuals.T)
        sigma = 0.5 * (sigma + sigma.T)
        
        # Checagem de condicionamento
        cond_sigma = np.linalg.cond(sigma)
        if cond_sigma > 1e8:
            print(f"   ⚠️  Sigma mal-condicionado (cond={cond_sigma:.2e}), adicionando ridge")
            sigma += 1e-4 * np.eye(self.n_vars)
        
        # PSD enforcement
        eigvals, eigvecs = np.linalg.eigh(sigma)
        eigvals[eigvals < 1e-8] = 1e-8
        self.sigma = (eigvecs @ np.diag(eigvals) @ eigvecs.T)
        
        # Armazenar priors
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        
        # Calcular IRFs estruturais normalizados
        self._calculate_irfs_structural_normalized()
        
        # Checar estabilidade
        self.stable = self._check_stability()
        
        if not self.stable:
            warnings.warn("⚠️  Modelo instável (raízes AR fora do círculo unitário)", UserWarning)
        
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
            'stable': self.stable,
            'cond_sigma': float(cond_sigma)
        }
        
        print(f"✅ BVAR v2.1 estimado: {self.n_vars} vars, {self.n_lags} lags, stable={self.stable}")
        return results
    
    def _check_stability(self) -> bool:
        """
        Verificar estabilidade (raízes do polinômio AR < 1)
        
        v2.1: Retorna True se estável
        """
        k = self.n_vars
        p = self.n_lags
        
        # Matrizes A1..Ap
        A = [self.beta[:, 1 + i * k: 1 + (i + 1) * k] for i in range(p)]
        
        # Forma companion
        F = np.zeros((k * p, k * p))
        F[:k, :k * p] = np.hstack(A)
        if p > 1:
            F[k:, :k * (p - 1)] = np.eye(k * (p - 1))
        
        # Eigenvalues
        eigvals = np.linalg.eigvals(F)
        max_eig = np.max(np.abs(eigvals))
        
        print(f"   Estabilidade: max|eig|={max_eig:.3f} {'✓' if max_eig < 1 else '✗'}")
        return bool(max_eig < 1.0)
    
    def _calculate_irfs_structural_normalized(self, max_horizon: int = 12):
        """
        IRFs estruturais NORMALIZADOS para 1 bps no Fed
        
        v2.1: Normaliza coluna 0 de L para choque de 1 bps no Fed
        """
        print("📊 Calculando IRFs estruturais normalizados (1 bps Fed)...")
        
        k = self.n_vars
        p = self.n_lags
        
        # Matrizes A1..Ap
        A = [self.beta[:, 1 + i * k: 1 + (i + 1) * k] for i in range(p)]
        
        # Companion
        F = np.zeros((k * p, k * p))
        F[:k, :k * p] = np.hstack(A)
        if p > 1:
            F[k:, :k * (p - 1)] = np.eye(k * (p - 1))
        
        # Cholesky com fallback
        try:
            L = np.linalg.cholesky(self.sigma + 1e-8 * np.eye(k))
        except np.linalg.LinAlgError:
            eigvals, eigvecs = np.linalg.eigh(self.sigma)
            eigvals[eigvals < 1e-8] = 1e-8
            sigma_psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
            L = np.linalg.cholesky(sigma_psd)
        
        # Normalização: choque estrutural do Fed = 1 bps
        scale = L[0, 0] if abs(L[0, 0]) > 1e-8 else 1.0
        L = L / scale
        
        # IRFs
        irf = np.zeros((max_horizon + 1, k, k))
        irf[0] = L
        
        Fpow = np.eye(k * p)
        for h in range(1, max_horizon + 1):
            Fpow = Fpow @ F
            irf[h] = (Fpow[:k, :k]) @ L
        
        self.irfs = {f'h_{h}': irf[h] for h in range(max_horizon + 1)}
        print(f"✅ IRFs calculados e normalizados (1 bps Fed → resposta Selic em bps)")
    
    def conditional_forecast(self, 
                           fed_path: List[float],
                           horizon_months: int = 12,
                           n_simulations: int = None,
                           extend_policy: Literal["hold", "zero"] = "hold") -> Dict[str, any]:
        """
        Previsão condicional dinâmica com multi-step consistente
        
        v2.1: Estado atualizado corretamente ao fim de cada horizonte
        
        Args:
            fed_path: Caminho Fed (bps)
            horizon_months: Horizonte
            n_simulations: Número de simulações
            extend_policy: "hold" (manter último) ou "zero" se horizon > len(path)
        """
        if n_simulations is None:
            n_simulations = self.n_simulations
        
        print(f"🔮 Previsão condicional dinâmica (extend_policy={extend_policy})...")
        
        k, p = self.n_vars, self.n_lags
        
        # Coeficientes
        A = [self.beta[:, 1 + i * k: 1 + (i + 1) * k] for i in range(p)]
        c = self.beta[:, 0]
        
        # Estado inicial
        Yhist = self.Y[-p:, :].copy() if self.Y.shape[0] >= p else np.zeros((p, k))
        
        forecasts = {}
        
        for h in range(1, min(horizon_months + 1, len(fed_path) + 1)):
            selic_draws = np.zeros(n_simulations)
            
            # Fed para este horizonte
            if h - 1 < len(fed_path):
                fed_imposed = fed_path[h - 1]
            else:
                if extend_policy == "hold":
                    fed_imposed = fed_path[-1] if fed_path else 0.0
                else:  # zero
                    fed_imposed = 0.0
            
            for s in range(n_simulations):
                y_stack = Yhist.copy()
                y_next = c.copy()
                
                # Contribuição lags
                for ell in range(1, p + 1):
                    y_next += A[ell - 1] @ y_stack[-ell, :]
                
                # Impor Fed
                y_next[0] = fed_imposed
                
                # Ruído via RNG local
                shock = self.rng.multivariate_normal(mean=np.zeros(k), cov=self.sigma)
                y_next = y_next + shock
                
                selic_draws[s] = y_next[1]
            
            # Estatísticas
            selic_mean = float(np.mean(selic_draws))
            
            forecasts[f'h_{h}'] = {
                'mean': selic_mean,
                'std': float(np.std(selic_draws, ddof=1)),
                'ci_lower': float(np.percentile(selic_draws, 2.5)),
                'ci_upper': float(np.percentile(selic_draws, 97.5)),
                'ci_80_lower': float(np.percentile(selic_draws, 10)),
                'ci_80_upper': float(np.percentile(selic_draws, 90)),
                'fed_imposed': float(fed_imposed),
                'n_simulations': n_simulations
            }
            
            # Atualizar estado APÓS loop de simulações (consistência)
            Yhist = np.vstack([Yhist, [fed_imposed, selic_mean]])[-p:, :]
            
            print(f"  h={h}: Selic {forecasts[f'h_{h}']['mean']:.1f} bps "
                  f"[{forecasts[f'h_{h}']['ci_lower']:.1f}, {forecasts[f'h_{h}']['ci_upper']:.1f}] "
                  f"| Fed={fed_imposed:.1f} bps")
        
        self.forecasts = forecasts
        return forecasts
    
    def scenario_analysis(self, scenarios: Dict[str, List[float]]) -> Dict[str, Dict[str, any]]:
        """Análise de cenários múltiplos"""
        print(f"📊 Análise de {len(scenarios)} cenários...")
        
        results = {}
        for scenario_name, fed_path in scenarios.items():
            print(f"  🔍 {scenario_name}")
            forecast = self.conditional_forecast(fed_path)
            
            results[scenario_name] = {
                'scenario_name': scenario_name,
                'fed_path': fed_path,
                'forecasts': forecast,
                'avg_selic_response': np.mean([f['mean'] for f in forecast.values()]),
                'max_selic_response': np.max([f['mean'] for f in forecast.values()]),
                'horizon_max_response': max(forecast.keys(), key=lambda k: forecast[k]['mean'])
            }
        
        return results
    
    def get_irf_summary(self) -> Dict[str, any]:
        """
        Resumo IRFs
        
        v2.1: Adiciona metadados de identificação
        """
        if not self.irfs:
            return {}
        
        summary = {
            'max_response': 0.0,
            'horizon_max_response': 0,
            'persistence': 0.0,
            'irf_values': {},
            'method': 'structural_cholesky',
            'chol_order': ['fed', 'selic'],
            'irf_unit': 'bps_per_bps',
            'normalized': True
        }
        
        max_response = 0
        horizon_max = 0
        
        for horizon, irf_matrix in self.irfs.items():
            selic_response = abs(irf_matrix[1, 0])
            summary['irf_values'][horizon] = selic_response
            
            if selic_response > max_response:
                max_response = selic_response
                horizon_max = int(horizon.split('_')[1])
        
        summary['max_response'] = max_response
        summary['horizon_max_response'] = horizon_max
        summary['persistence'] = sum(summary['irf_values'].values())
        
        return summary
    
    def evaluate_model(self) -> Dict[str, any]:
        """
        Avaliar modelo
        
        v2.1: Adiciona estabilidade e metadados completos
        """
        if self.beta is None:
            return {'error': 'Modelo não estimado'}
        
        # R²
        Y_pred = self.X @ self.beta.T
        ss_res = np.sum((self.Y - Y_pred) ** 2)
        ss_tot = np.sum((self.Y - np.mean(self.Y, axis=0)) ** 2)
        r_squared = 1 - ss_res / ss_tot
        
        irf_summary = self.get_irf_summary()
        
        evaluation = {
            'r_squared': r_squared,
            'n_obs': self.Y.shape[0],
            'n_vars': self.n_vars,
            'n_lags': self.n_lags,
            'stable': self.stable,
            'irf_summary': irf_summary,
            'prior_strength': float(np.trace(self.prior_var) / (np.trace(np.linalg.pinv(self.prior_var)) + 1e-8)),
            'model_quality': 'good' if np.mean(r_squared) > 0.3 else 'moderate' if np.mean(r_squared) > 0.1 else 'weak',
            'sigma_condition_number': float(np.linalg.cond(self.sigma)),
            'identification': 'cholesky_fed_first',
            'chol_order': ['fed', 'selic'],
            'priors_profile': self.priors_profile,
            'random_state': self.random_state
        }
        
        return evaluation
    
    def to_dict(self) -> Dict[str, any]:
        """
        Serializar para dict (JSON-friendly)
        
        v2.1: Para auditoria e compatibilidade API
        """
        return {
            'model_type': 'BVAR_Minnesota_v2.1',
            'n_vars': self.n_vars,
            'n_lags': self.n_lags,
            'random_state': self.random_state,
            'priors_profile': self.priors_profile,
            'minnesota_params': self.minnesota_params,
            'beta': self.beta.tolist() if self.beta is not None else None,
            'sigma': self.sigma.tolist() if self.sigma is not None else None,
            'train_dates': self.train_dates,
            'scale_info': self.scale_info,
            'stable': self.stable,
            'evaluation': self.evaluate_model() if self.beta is not None else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'BVARMinnesota':
        """
        Carregar de dict
        
        v2.1: Reconstruir modelo de JSON
        """
        model = cls(
            n_lags=data['n_lags'],
            n_vars=data['n_vars'],
            minnesota_params=data['minnesota_params'],
            random_state=data['random_state'],
            priors_profile=data.get('priors_profile', 'custom')
        )
        
        if data['beta'] is not None:
            model.beta = np.array(data['beta'])
        if data['sigma'] is not None:
            model.sigma = np.array(data['sigma'])
        
        model.train_dates = data.get('train_dates')
        model.scale_info = data.get('scale_info')
        model.stable = data.get('stable')
        
        return model


if __name__ == "__main__":
    print("🧪 Testando BVAR Minnesota v2.1 (ajustes de robustez)...")
    
    np.random.seed(42)
    n = 50
    
    fed_moves = np.random.normal(0, 25, n)
    selic_moves = 0.3 * fed_moves + np.random.normal(0, 15, n)
    dates = pd.date_range('2020-01-01', periods=n, freq='M')
    
    bvar = BVARMinnesota(
        n_lags=2, 
        n_vars=2,
        random_state=42,
        priors_profile="small-N-default"
    )
    
    Y, X = bvar.prepare_data(
        fed_data=pd.Series(fed_moves),
        selic_data=pd.Series(selic_moves),
        fed_dates=dates,
        selic_dates=dates
    )
    
    results = bvar.estimate()
    evaluation = bvar.evaluate_model()
    
    print(f"\n📊 Avaliação v2.1:")
    print(f"  R² médio: {np.mean(evaluation['r_squared']):.3f}")
    print(f"  Estável: {evaluation['stable']}")
    print(f"  Qualidade: {evaluation['model_quality']}")
    print(f"  Cond(Sigma): {evaluation['sigma_condition_number']:.2f}")
    
    print(f"\n📈 IRFs:")
    irf = evaluation['irf_summary']
    print(f"  Máx: {irf['max_response']:.3f} @ h={irf['horizon_max_response']}")
    print(f"  Normalizado: {irf['normalized']}, Unidade: {irf['irf_unit']}")
    
    # Teste condicional
    fed_scenario = [25, 0, -25, 0]
    forecast = bvar.conditional_forecast(fed_scenario, horizon_months=4)
    
    # Serialização
    model_dict = bvar.to_dict()
    print(f"\n💾 Serialização: {len(json.dumps(model_dict))} chars")
    
    print("\n✅ v2.1 completo!")
    print("🎯 Ajustes implementados:")
    print("  ✓ RNG local")
    print("  ✓ Estado multi-step consistente")
    print("  ✓ IRFs normalizados (1 bps)")
    print("  ✓ Checagem de estabilidade")
    print("  ✓ Serialização JSON")
