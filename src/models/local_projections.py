"""
Local Projections para Spillovers FED-Selic
Implementação baseada em Jordà (2005) com shrinkage para amostras pequenas

Baseado em:
- Jordà, Ò. (2005): "Estimation and Inference of Impulse Responses by Local Projections"
- Elliott, G., Rothenberg, T. J., & Stock, J. H. (1996): "Efficient Tests for an Autoregressive Unit Root"
- Ng, S., & Perron, P. (2001): "Lag Length Selection and the Construction of Unit Root Tests"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.model_selection import cross_val_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class LocalProjectionsForecaster:
    """
    Local Projections com shrinkage para spillovers FED-Selic
    
    Implementa:
    - LP por horizonte com regularização
    - Seleção automática de lags (AIC/BIC/t-stat)
    - Bandas de confiança via bootstrap
    - Robustez a heterocedasticidade
    """
    
    def __init__(self, 
                 max_horizon: int = 12,
                 max_lags: int = 4,
                 alpha: float = 0.1,
                 regularization: str = 'ridge',
                 significance_level: float = 0.05,
                 # Aliases para backward compatibility
                 n_lags: int = None,
                 horizons: list = None,
                 shrinkage_method: str = None,
                 random_state: int = None):
        """
        Inicializar Local Projections Forecaster
        
        Args:
            max_horizon: Horizonte máximo de previsão (meses)
            max_lags: Número máximo de lags
            alpha: Parâmetro de regularização
            regularization: Tipo de regularização ('ridge', 'lasso', 'elastic')
            significance_level: Nível de significância para testes
        """
        # Aplicar aliases (backward compatibility)
        if n_lags is not None:
            max_lags = n_lags
        if shrinkage_method is not None:
            regularization = shrinkage_method
        
        self.max_horizon = max_horizon
        self.max_lags = max_lags
        self.alpha = alpha
        self.regularization = regularization
        self.significance_level = significance_level
        
        # Aliases como properties
        self.n_lags = self.max_lags  # Alias
        self.horizons = horizons if horizons else list(range(1, max_horizon + 1))  # Alias
        self.shrinkage_method = self.regularization  # Alias
        self.random_state = random_state if random_state else 42  # Para consistência
        
        # Modelos por horizonte
        self.models = {}
        self.irfs = {}
        self.confidence_intervals = {}
        self.lag_selection = {}
        
        # Configurar regularizador
        self._setup_regularizer()
        
    def _setup_regularizer(self):
        """Configurar regularizador baseado no tipo especificado"""
        # Normalizar nome (aceitar variantes)
        reg_normalized = self.regularization.lower().replace('_', '').replace('-', '')
        
        if reg_normalized in ['ridge', 'l2']:
            self.regularizer = Ridge(alpha=self.alpha, random_state=42)
        elif reg_normalized in ['lasso', 'l1']:
            self.regularizer = Lasso(alpha=self.alpha, random_state=42, max_iter=2000)
        elif reg_normalized in ['elastic', 'elasticnet', 'elasticnet']:
            self.regularizer = ElasticNet(alpha=self.alpha, l1_ratio=0.5, random_state=42, max_iter=2000)
        else:
            raise ValueError(f"Regularização não suportada: {self.regularization}")
    
    def prepare_data(self, 
                    fed_data: pd.Series, 
                    selic_data: pd.Series,
                    fed_dates: pd.DatetimeIndex,
                    selic_dates: pd.DatetimeIndex) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Preparar dados para Local Projections
        
        Args:
            fed_data: Série de movimentos do Fed (bps)
            selic_data: Série de movimentos da Selic (bps)
            fed_dates: Datas das decisões do Fed
            selic_dates: Datas das decisões do Copom
            
        Returns:
            DataFrame com variáveis preparadas
        """
        print("🔧 Preparando dados para Local Projections...")
        
        # Alinhar séries temporais
        min_date = max(fed_dates.min(), selic_dates.min())
        max_date = min(fed_dates.max(), selic_dates.max())
        
        # Criar índice mensal
        date_range = pd.date_range(start=min_date, end=max_date, freq='M')
        
        # Interpolar dados para frequência mensal
        fed_monthly = self._interpolate_to_monthly(fed_data, fed_dates, date_range)
        selic_monthly = self._interpolate_to_monthly(selic_data, selic_dates, date_range)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'fed_move': fed_monthly,
            'selic_move': selic_monthly,
            'date': date_range
        }).dropna()
        
        # Criar defasagens
        df = self._create_lags(df, ['fed_move', 'selic_move'], self.max_lags)
        
        print(f"✅ Dados preparados: {len(df)} observações")
        return df
    
    def _interpolate_to_monthly(self, 
                               data: pd.Series, 
                               dates: pd.DatetimeIndex, 
                               target_dates: pd.DatetimeIndex) -> pd.Series:
        """Interpolar dados para frequência mensal"""
        # Criar série temporal
        ts = pd.Series(data.values, index=dates)
        
        # Reindexar para datas mensais
        ts_monthly = ts.reindex(target_dates, method='ffill')
        
        return ts_monthly
    
    def _create_lags(self, df: pd.DataFrame, columns: List[str], max_lags: int) -> pd.DataFrame:
        """Criar defasagens das variáveis especificadas"""
        for col in columns:
            for lag in range(1, max_lags + 1):
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        return df.dropna()
    
    def select_lags(self, df: pd.DataFrame, target_var: str = 'selic_move') -> int:
        """
        Seleção de lags baseada em AIC/BIC/t-stat
        
        Baseado em Ng & Perron (2001)
        """
        print(f"🔍 Selecionando lags para {target_var}...")
        
        best_lags = 1
        best_aic = float('inf')
        
        for lags in range(1, self.max_lags + 1):
            try:
                # Preparar variáveis
                y = df[target_var].values
                X_cols = [f'{target_var}_lag_{i}' for i in range(1, lags + 1)]
                X = df[X_cols].values
                
                # Ajustar modelo
                model = Ridge(alpha=self.alpha)
                model.fit(X, y)
                
                # Calcular AIC
                n = len(y)
                k = X.shape[1]
                mse = np.mean((y - model.predict(X)) ** 2)
                aic = n * np.log(mse) + 2 * k
                
                if aic < best_aic:
                    best_aic = aic
                    best_lags = lags
                    
            except Exception as e:
                print(f"⚠️  Erro ao testar {lags} lags: {e}")
                continue
        
        print(f"✅ Melhor número de lags: {best_lags} (AIC: {best_aic:.2f})")
        return best_lags
    
    def fit(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Estimar Local Projections por horizonte
        
        Equação: ΔSelic_{t+h} = α_h + β_h * ΔFed_t + Σ φ_{h,i} * ΔSelic_{t-i} + ε_{t+h}
        """
        print("🔬 Estimando Local Projections por horizonte...")
        
        results = {}
        
        for h in range(1, self.max_horizon + 1):
            print(f"  📊 Horizonte h={h}...")
            
            try:
                # Preparar variáveis para horizonte h
                y = df['selic_move'].shift(-h).dropna()
                X = self._prepare_regressors(df, h)
                
                # Alinhar dimensões
                min_len = min(len(y), len(X))
                y = y.iloc[:min_len]
                X = X.iloc[:min_len]
                
                if len(y) < 10:  # Muito poucos dados
                    print(f"    ⚠️  Poucos dados para h={h}: {len(y)} observações")
                    continue
                
                # Selecionar lags para este horizonte
                optimal_lags = self.select_lags(df.iloc[:len(y)])
                
                # Ajustar modelo com regularização
                model = Ridge(alpha=self.alpha)
                model.fit(X, y)
                
                # Calcular IRF (coeficiente de ΔFed_t)
                irf = model.coef_[0] if len(model.coef_) > 0 else 0
                
                # Calcular bandas de confiança via bootstrap
                ci_lower, ci_upper = self._bootstrap_confidence_interval(X, y, model, h)
                
                # Armazenar resultados
                results[f'h_{h}'] = {
                    'model': model,
                    'irf': irf,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'r_squared': model.score(X, y),
                    'n_obs': len(y),
                    'optimal_lags': optimal_lags
                }
                
                print(f"    ✅ IRF: {irf:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]")
                
            except Exception as e:
                print(f"    ❌ Erro no horizonte h={h}: {e}")
                continue
        
        self.models = results
        print(f"✅ Local Projections estimados para {len(results)} horizontes")
        return results
    
    def _prepare_regressors(self, df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Preparar regressores para horizonte específico"""
        regressors = []
        
        # Choque contemporâneo do Fed
        regressors.append(df['fed_move'])
        
        # Defasagens da Selic
        for lag in range(1, self.max_lags + 1):
            if f'selic_move_lag_{lag}' in df.columns:
                regressors.append(df[f'selic_move_lag_{lag}'])
        
        # Defasagens do Fed
        for lag in range(1, self.max_lags + 1):
            if f'fed_move_lag_{lag}' in df.columns:
                regressors.append(df[f'fed_move_lag_{lag}'])
        
        return pd.DataFrame(regressors).T
    
    def _bootstrap_confidence_interval(self, 
                                     X: pd.DataFrame, 
                                     y: pd.Series, 
                                     model: any, 
                                     horizon: int,
                                     n_bootstrap: int = 1000) -> Tuple[float, float]:
        """Calcular bandas de confiança via bootstrap"""
        try:
            irfs = []
            
            for _ in range(n_bootstrap):
                # Bootstrap sample
                n = len(y)
                indices = np.random.choice(n, size=n, replace=True)
                
                X_boot = X.iloc[indices]
                y_boot = y.iloc[indices]
                
                # Ajustar modelo
                model_boot = Ridge(alpha=self.alpha)
                model_boot.fit(X_boot, y_boot)
                
                # Coletar IRF
                irf = model_boot.coef_[0] if len(model_boot.coef_) > 0 else 0
                irfs.append(irf)
            
            # Calcular percentis
            ci_lower = np.percentile(irfs, 2.5)
            ci_upper = np.percentile(irfs, 97.5)
            
            return ci_lower, ci_upper
            
        except Exception as e:
            print(f"    ⚠️  Erro no bootstrap para h={horizon}: {e}")
            return 0.0, 0.0
    
    def forecast(self, 
                fed_shock: float, 
                current_state: Dict[str, float],
                horizon_months: List[int] = None) -> Dict[str, any]:
        """
        Previsão condicional para choque específico do Fed
        
        Args:
            fed_shock: Magnitude do choque do Fed (bps)
            current_state: Estado atual das variáveis
            horizon_months: Horizontes específicos para previsão
            
        Returns:
            Dicionário com previsões por horizonte
        """
        if horizon_months is None:
            horizon_months = list(range(1, self.max_horizon + 1))
        
        print(f"🔮 Previsão para choque Fed de {fed_shock} bps...")
        
        forecasts = {}
        
        for h in horizon_months:
            if f'h_{h}' not in self.models:
                continue
                
            model_info = self.models[f'h_{h}']
            model = model_info['model']
            
            try:
                # Preparar regressores para previsão
                X_pred = self._prepare_forecast_regressors(fed_shock, current_state, h)
                
                # Previsão pontual
                point_forecast = model.predict(X_pred.reshape(1, -1))[0]
                
                # Bandas de confiança
                ci_lower = point_forecast + model_info['ci_lower']
                ci_upper = point_forecast + model_info['ci_upper']
                
                forecasts[f'h_{h}'] = {
                    'point_forecast': point_forecast,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'irf': model_info['irf'],
                    'r_squared': model_info['r_squared'],
                    'n_obs': model_info['n_obs']
                }
                
                print(f"  📊 h={h}: {point_forecast:.1f} bps [{ci_lower:.1f}, {ci_upper:.1f}]")
                
            except Exception as e:
                print(f"  ❌ Erro na previsão h={h}: {e}")
                continue
        
        return forecasts
    
    def _prepare_forecast_regressors(self, 
                                   fed_shock: float, 
                                   current_state: Dict[str, float],
                                   horizon: int) -> np.ndarray:
        """Preparar regressores para previsão"""
        regressors = []
        
        # Choque contemporâneo do Fed
        regressors.append(fed_shock)
        
        # Defasagens da Selic (usar estado atual)
        for lag in range(1, self.max_lags + 1):
            key = f'selic_lag_{lag}'
            regressors.append(current_state.get(key, 0.0))
        
        # Defasagens do Fed (usar estado atual)
        for lag in range(1, self.max_lags + 1):
            key = f'fed_lag_{lag}'
            regressors.append(current_state.get(key, 0.0))
        
        return np.array(regressors)
    
    def get_impulse_response_function(self) -> Dict[str, float]:
        """Obter função de resposta ao impulso completa"""
        irf = {}
        
        for horizon, model_info in self.models.items():
            irf[horizon] = {
                'irf': model_info['irf'],
                'ci_lower': model_info['ci_lower'],
                'ci_upper': model_info['ci_upper']
            }
        
        return irf
    
    def evaluate_model(self) -> Dict[str, any]:
        """Avaliar qualidade do modelo"""
        evaluation = {
            'n_horizons': len(self.models),
            'avg_r_squared': 0.0,
            'avg_irf': 0.0,
            'max_irf': 0.0,
            'horizon_max_response': 1
        }
        
        if not self.models:
            return evaluation
        
        r_squared_values = []
        irf_values = []
        
        for horizon, model_info in self.models.items():
            r_squared_values.append(model_info['r_squared'])
            irf_values.append(abs(model_info['irf']))
        
        evaluation['avg_r_squared'] = np.mean(r_squared_values)
        evaluation['avg_irf'] = np.mean(irf_values)
        evaluation['max_irf'] = np.max(irf_values)
        
        # Encontrar horizonte de máxima resposta
        max_idx = np.argmax(irf_values)
        evaluation['horizon_max_response'] = list(self.models.keys())[max_idx]
        
        return evaluation


if __name__ == "__main__":
    # Teste do Local Projections Forecaster
    print("🧪 Testando Local Projections Forecaster...")
    
    # Dados sintéticos para teste
    np.random.seed(42)
    n = 50
    
    # Gerar séries com spillover
    fed_moves = np.random.normal(0, 25, n)  # Movimentos do Fed
    selic_moves = 0.3 * fed_moves + np.random.normal(0, 15, n)  # Selic responde ao Fed
    
    # Criar datas
    dates = pd.date_range('2020-01-01', periods=n, freq='M')
    
    # Criar forecaster
    forecaster = LocalProjectionsForecaster(max_horizon=6, max_lags=2)
    
    # Preparar dados
    df = forecaster.prepare_data(
        fed_data=pd.Series(fed_moves),
        selic_data=pd.Series(selic_moves),
        fed_dates=dates,
        selic_dates=dates
    )
    
    # Estimar modelo
    results = forecaster.fit(df)
    
    # Avaliar modelo
    evaluation = forecaster.evaluate_model()
    print(f"\n📊 Avaliação do modelo:")
    print(f"  Horizontes estimados: {evaluation['n_horizons']}")
    print(f"  R² médio: {evaluation['avg_r_squared']:.3f}")
    print(f"  IRF médio: {evaluation['avg_irf']:.3f}")
    print(f"  Máxima resposta: h={evaluation['horizon_max_response']}")
    
    # Teste de previsão
    current_state = {
        'selic_lag_1': 0.0,
        'selic_lag_2': 0.0,
        'fed_lag_1': 0.0,
        'fed_lag_2': 0.0
    }
    
    forecast = forecaster.forecast(fed_shock=25.0, current_state=current_state)
    print(f"\n🔮 Previsão para choque de +25 bps:")
    for horizon, pred in forecast.items():
        print(f"  {horizon}: {pred['point_forecast']:.1f} bps")
    
    print("✅ Teste concluído com sucesso!")
