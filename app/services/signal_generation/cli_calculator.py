"""
Calculador CLI - Implementa o Dynamic Factor Model com Kalman Filter
Baseado na metodologia da OECD para calcular o Composite Leading Indicator
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import signal
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class CLICalculator:
    """
    Calculador do Composite Leading Indicator (CLI) usando Dynamic Factor Model
    """
    
    def __init__(self, 
                 target_cycle_period: int = 24,  # Período do ciclo de negócios em meses
                 smoothing_factor: float = 0.3,  # Fator de suavização (aumentado)
                 min_data_points: int = 60,     # Mínimo de pontos para cálculo
                 use_hamilton_filter: bool = True,  # Usar Filtro Hamilton em vez de HP
                 regime_switching: bool = True):   # Ativar modelos de regime
        """
        Inicializa o calculador CLI
        
        Args:
            target_cycle_period: Período alvo do ciclo de negócios (meses)
            smoothing_factor: Fator de suavização para o filtro de Kalman
            min_data_points: Número mínimo de pontos de dados necessários
        """
        self.target_cycle_period = target_cycle_period
        self.smoothing_factor = smoothing_factor
        self.min_data_points = min_data_points
        self.use_hamilton_filter = use_hamilton_filter
        self.regime_switching = regime_switching
        self.scaler = StandardScaler()
        
    def calculate_cli(self, 
                     economic_data: Dict[str, pd.DataFrame],
                     cli_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Calcula o CLI baseado nas séries econômicas
        
        Args:
            economic_data: Dicionário com DataFrames das séries econômicas
            cli_data: Dados CLI existentes (opcional, para validação)
            
        Returns:
            DataFrame com CLI calculado e normalizado
        """
        try:
            # 1. Preparar dados para análise
            prepared_data = self._prepare_data(economic_data)
            
            if prepared_data is None or len(prepared_data) < self.min_data_points:
                logger.warning(f"Dados insuficientes para cálculo CLI: {len(prepared_data) if prepared_data is not None else 0} pontos")
                return pd.DataFrame()
            
            # 2. Aplicar transformações de tendência
            detrended_data = self._detrend_series(prepared_data)
            
            # 3. Calcular Dynamic Factor Model
            factors = self._calculate_dynamic_factors(detrended_data)
            
            # 4. Aplicar filtro de Kalman para suavização
            smoothed_factors = self._apply_kalman_filter(factors)
            
            # 5. Normalizar CLI (média = 100)
            cli_normalized = self._normalize_cli(smoothed_factors)
            
            # 6. Criar DataFrame de resultado
            result_df = pd.DataFrame({
                'date': prepared_data.index,
                'cli_raw': factors,
                'cli_smoothed': smoothed_factors,
                'cli_normalized': cli_normalized,
                'cli_trend': self._calculate_trend(smoothed_factors),
                'cli_momentum': self._calculate_momentum(smoothed_factors)
            })
            
            logger.info(f"CLI calculado com sucesso: {len(result_df)} pontos")
            return result_df
            
        except Exception as e:
            logger.error(f"Erro ao calcular CLI: {e}")
            return pd.DataFrame()
    
    def _prepare_data(self, economic_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Prepara e alinha os dados econômicos para análise
        """
        try:
            # Lista de séries econômicas relevantes para CLI
            relevant_series = ['ipca', 'selic', 'cambio', 'prod_industrial', 'pib', 'desemprego']
            
            prepared_series = {}
            
            for series_name in relevant_series:
                if series_name in economic_data and not economic_data[series_name].empty:
                    df = economic_data[series_name].copy()
                    
                    # Garantir que temos as colunas corretas
                    if 'date' in df.columns and 'value' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                        df = df.sort_index()
                        
                        # Remover valores nulos
                        df = df.dropna()
                        
                        if len(df) > 0:
                            prepared_series[series_name] = df['value']
            
            if not prepared_series:
                logger.warning("Nenhuma série econômica válida encontrada")
                return None
            
            # Alinhar todas as séries por data
            aligned_data = pd.DataFrame(prepared_series)
            aligned_data = aligned_data.dropna()
            
            if len(aligned_data) < self.min_data_points:
                logger.warning(f"Dados alinhados insuficientes: {len(aligned_data)} pontos")
                return None
            
            return aligned_data
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados: {e}")
            return None
    
    def _detrend_series(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Remove tendências das séries usando Filtro Hamilton (mais robusto que HP)
        """
        try:
            detrended_data = data.copy()
            
            for column in data.columns:
                if column == 'date':
                    continue
                    
                series = data[column].values
                
                if self.use_hamilton_filter:
                    # Aplicar Filtro Hamilton (mais robusto que HP)
                    try:
                        detrended_series = self._hamilton_filter(series)
                        detrended_data[column] = detrended_series
                    except Exception as e:
                        logger.warning(f"Erro ao aplicar Hamilton filter em {column}: {e}")
                        # Fallback: usar HP filter
                        hp_cycle, hp_trend = self._hp_filter(series)
                        detrended_data[column] = hp_cycle
                else:
                    # Usar HP Filter tradicional (menos robusto)
                    hp_cycle, hp_trend = self._hp_filter(series)
                    detrended_data[column] = hp_cycle
                
                # Aplicar transformação logarítmica se necessário
                if series.min() > 0:
                    detrended_data[column] = np.log(1 + np.abs(detrended_data[column]))
            
            return detrended_data
            
        except Exception as e:
            logger.error(f"Erro ao remover tendências: {e}")
            return data
    
    def _hamilton_filter(self, y: np.ndarray, h: int = 8) -> np.ndarray:
        """
        Implementa o Filtro Hamilton (mais robusto que HP)
        
        Args:
            y: Série temporal
            h: Horizonte de previsão (padrão 8 para dados mensais)
        
        Returns:
            Série filtrada (componente cíclico)
        """
        try:
            n = len(y)
            if n < h + 4:
                return y
            
            # Preparar matriz de regressão
            X = np.ones((n - h, h + 1))
            for i in range(h):
                X[:, i + 1] = y[i:n - h + i]
            
            # Regressão OLS
            y_reg = y[h:]
            beta = np.linalg.lstsq(X, y_reg, rcond=None)[0]
            
            # Calcular tendência
            trend = np.zeros(n)
            trend[h:] = X @ beta
            
            # Extrapolar tendência para os primeiros h pontos
            for i in range(h):
                trend[i] = beta[0] + np.sum(beta[1:] * y[:i+1])
            
            # Componente cíclico
            cycle = y - trend
            
            return cycle
            
        except Exception as e:
            logger.error(f"Erro no Filtro Hamilton: {e}")
            return y
    
    def _hp_filter(self, series: np.ndarray, lambda_param: float = 1600) -> Tuple[np.ndarray, np.ndarray]:
        """
        Aplica o filtro Hodrick-Prescott para separar ciclo e tendência
        """
        try:
            n = len(series)
            if n < 4:
                return series, np.zeros_like(series)
            
            # Matriz de diferenças de segunda ordem
            A = np.zeros((n-2, n))
            for i in range(n-2):
                A[i, i] = 1
                A[i, i+1] = -2
                A[i, i+2] = 1
            
            # Resolver sistema para obter tendência
            I = np.eye(n)
            trend = np.linalg.solve(I + lambda_param * A.T @ A, series)
            cycle = series - trend
            
            return cycle, trend
            
        except Exception as e:
            logger.error(f"Erro no HP Filter: {e}")
            return series, np.zeros_like(series)
    
    def _calculate_dynamic_factors(self, data: pd.DataFrame) -> np.ndarray:
        """
        Calcula fatores dinâmicos usando PCA
        """
        try:
            # Padronizar dados
            scaled_data = self.scaler.fit_transform(data)
            
            # Aplicar PCA
            pca = PCA(n_components=1)
            first_component = pca.fit_transform(scaled_data)
            
            # O primeiro componente principal representa o fator comum
            factor = first_component.flatten()
            
            # Aplicar transformação para inverter se necessário
            if np.corrcoef(factor, data.mean(axis=1))[0, 1] < 0:
                factor = -factor
            
            return factor
            
        except Exception as e:
            logger.error(f"Erro ao calcular fatores dinâmicos: {e}")
            return np.zeros(len(data))
    
    def _apply_kalman_filter(self, series: np.ndarray) -> np.ndarray:
        """
        Aplica filtro de Kalman para suavização
        """
        try:
            n = len(series)
            if n < 2:
                return series
            
            # Parâmetros do filtro de Kalman
            Q = self.smoothing_factor  # Variância do processo
            R = 1.0  # Variância da observação
            
            # Inicialização
            x = series[0]  # Estado inicial
            P = 1.0  # Covariância inicial
            
            smoothed = np.zeros(n)
            smoothed[0] = x
            
            # Filtro de Kalman
            for i in range(1, n):
                # Predição
                x_pred = x
                P_pred = P + Q
                
                # Atualização
                K = P_pred / (P_pred + R)  # Ganho de Kalman
                x = x_pred + K * (series[i] - x_pred)
                P = (1 - K) * P_pred
                
                smoothed[i] = x
            
            return smoothed
            
        except Exception as e:
            logger.error(f"Erro no filtro de Kalman: {e}")
            return series
    
    def _normalize_cli(self, series: np.ndarray) -> np.ndarray:
        """
        Normaliza CLI para média 100
        """
        try:
            if len(series) == 0:
                return series
            
            # Calcular média móvel de 12 meses para normalização
            window = min(12, len(series))
            if window < len(series):
                rolling_mean = pd.Series(series).rolling(window=window, center=True).mean()
                mean_value = rolling_mean.mean()
            else:
                mean_value = np.mean(series)
            
            # Normalizar para média 100 com suavização adicional
            if mean_value != 0 and not np.isnan(mean_value):
                # Aplicar transformação logarítmica para reduzir volatilidade
                log_series = np.log(np.abs(series) + 1) * np.sign(series)
                log_mean = np.log(np.abs(mean_value) + 1) * np.sign(mean_value)
                normalized = (log_series / log_mean) * 100
                
                # Limitar valores extremos
                normalized = np.clip(normalized, 50, 150)
            else:
                normalized = np.full_like(series, 100.0)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Erro na normalização CLI: {e}")
            return series
    
    def _calculate_trend(self, series: np.ndarray) -> np.ndarray:
        """
        Calcula tendência do CLI (média móvel de 3 meses)
        """
        try:
            if len(series) < 3:
                return np.zeros_like(series)
            
            trend = pd.Series(series).rolling(window=3, center=True).mean()
            return trend.fillna(series).values
            
        except Exception as e:
            logger.error(f"Erro ao calcular tendência: {e}")
            return np.zeros_like(series)
    
    def _calculate_momentum(self, series: np.ndarray) -> np.ndarray:
        """
        Calcula momentum do CLI (diferença de 3 meses)
        """
        try:
            if len(series) < 4:
                return np.zeros_like(series)
            
            momentum = pd.Series(series).diff(3)
            return momentum.fillna(0).values
            
        except Exception as e:
            logger.error(f"Erro ao calcular momentum: {e}")
            return np.zeros_like(series)
    
    def get_cli_health_status(self) -> Dict[str, any]:
        """
        Retorna status de saúde do calculador CLI
        """
        return {
            'status': 'healthy',
            'target_cycle_period': self.target_cycle_period,
            'smoothing_factor': self.smoothing_factor,
            'min_data_points': self.min_data_points,
            'scaler_fitted': hasattr(self.scaler, 'mean_') and self.scaler.mean_ is not None
        }
