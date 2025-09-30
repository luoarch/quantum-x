"""
Data Processor Service - Single Responsibility Principle
Serviço responsável por processamento de dados
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.interfaces import IDataProcessor
from src.core.exceptions import DataError

class DataProcessorService(IDataProcessor):
    """
    Serviço de processamento de dados
    
    Responsabilidades:
    - Alinhar dados Fed-Selic
    - Criar features de lag
    - Detectar e tratar outliers
    - Aplicar transformações
    """
    
    def __init__(self, processing_config: Dict[str, Any] = None):
        self.config = processing_config or {}
        self.outlier_threshold = self.config.get('outlier_threshold', 3.0)
        self.max_lags = self.config.get('max_lags', 4)
    
    async def align_fed_selic_data(self, 
                                 fed_data: pd.DataFrame, 
                                 selic_data: pd.DataFrame) -> pd.DataFrame:
        """Alinhar dados Fed-Selic por data"""
        try:
            # Verificar se as colunas de data existem
            if 'date' not in fed_data.columns or 'date' not in selic_data.columns:
                raise DataError("Coluna 'date' não encontrada nos dados")
            
            # Converter para datetime
            fed_data['date'] = pd.to_datetime(fed_data['date'])
            selic_data['date'] = pd.to_datetime(selic_data['date'])
            
            # Definir data como índice
            fed_data = fed_data.set_index('date')
            selic_data = selic_data.set_index('date')
            
            # Alinhar por data (inner join)
            aligned_data = pd.merge(
                fed_data, selic_data, 
                left_index=True, right_index=True, 
                how='inner', suffixes=('_fed', '_selic')
            )
            
            # Verificar se há dados alinhados
            if aligned_data.empty:
                raise DataError("Nenhum dado alinhado encontrado entre Fed e Selic")
            
            # Resetar índice para ter coluna date
            aligned_data = aligned_data.reset_index()
            
            return aligned_data
            
        except Exception as e:
            raise DataError(f"Erro no alinhamento de dados: {str(e)}")
    
    async def create_lag_features(self, 
                                data: pd.DataFrame, 
                                max_lags: int) -> pd.DataFrame:
        """Criar features de lag"""
        try:
            # Verificar se há colunas numéricas para lag
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                raise DataError("Nenhuma coluna numérica encontrada para criar lags")
            
            # Criar cópia dos dados
            data_with_lags = data.copy()
            
            # Criar lags para cada coluna numérica
            for col in numeric_columns:
                for lag in range(1, max_lags + 1):
                    lag_col_name = f"{col}_lag_{lag}"
                    data_with_lags[lag_col_name] = data[col].shift(lag)
            
            # Remover linhas com NaN (devido aos lags)
            data_with_lags = data_with_lags.dropna()
            
            return data_with_lags
            
        except Exception as e:
            raise DataError(f"Erro na criação de features de lag: {str(e)}")
    
    async def detect_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detectar e tratar outliers"""
        try:
            # Verificar se há colunas numéricas
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return data  # Nenhuma coluna numérica para processar
            
            # Criar cópia dos dados
            cleaned_data = data.copy()
            
            # Detectar outliers usando IQR
            for col in numeric_columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Definir limites
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Identificar outliers
                outlier_mask = (data[col] < lower_bound) | (data[col] > upper_bound)
                
                # Tratar outliers (opção: remover ou substituir por valores limite)
                if self.config.get('outlier_treatment') == 'remove':
                    cleaned_data = cleaned_data[~outlier_mask]
                elif self.config.get('outlier_treatment') == 'cap':
                    cleaned_data.loc[data[col] < lower_bound, col] = lower_bound
                    cleaned_data.loc[data[col] > upper_bound, col] = upper_bound
                elif self.config.get('outlier_treatment') == 'winsorize':
                    # Winsorização: substituir por percentis
                    p5 = data[col].quantile(0.05)
                    p95 = data[col].quantile(0.95)
                    cleaned_data.loc[data[col] < p5, col] = p5
                    cleaned_data.loc[data[col] > p95, col] = p95
            
            return cleaned_data
            
        except Exception as e:
            raise DataError(f"Erro na detecção de outliers: {str(e)}")
    
    async def apply_transformations(self, data: pd.DataFrame, 
                                  transformations: Dict[str, str]) -> pd.DataFrame:
        """Aplicar transformações aos dados"""
        try:
            transformed_data = data.copy()
            
            for column, transformation in transformations.items():
                if column not in transformed_data.columns:
                    continue
                
                if transformation == 'log':
                    # Log transformação (adicionar constante para evitar log(0))
                    min_val = transformed_data[column].min()
                    if min_val <= 0:
                        transformed_data[column] = np.log(transformed_data[column] - min_val + 1)
                    else:
                        transformed_data[column] = np.log(transformed_data[column])
                
                elif transformation == 'sqrt':
                    # Raiz quadrada
                    transformed_data[column] = np.sqrt(np.abs(transformed_data[column]))
                
                elif transformation == 'diff':
                    # Primeira diferença
                    transformed_data[column] = transformed_data[column].diff()
                
                elif transformation == 'pct_change':
                    # Mudança percentual
                    transformed_data[column] = transformed_data[column].pct_change()
                
                elif transformation == 'standardize':
                    # Padronização (z-score)
                    mean_val = transformed_data[column].mean()
                    std_val = transformed_data[column].std()
                    if std_val > 0:
                        transformed_data[column] = (transformed_data[column] - mean_val) / std_val
                
                elif transformation == 'normalize':
                    # Normalização min-max
                    min_val = transformed_data[column].min()
                    max_val = transformed_data[column].max()
                    if max_val > min_val:
                        transformed_data[column] = (transformed_data[column] - min_val) / (max_val - min_val)
            
            return transformed_data
            
        except Exception as e:
            raise DataError(f"Erro na aplicação de transformações: {str(e)}")
    
    async def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validar qualidade dos dados"""
        try:
            quality_report = {
                "total_rows": len(data),
                "total_columns": len(data.columns),
                "missing_values": data.isnull().sum().to_dict(),
                "duplicate_rows": data.duplicated().sum(),
                "data_types": data.dtypes.to_dict(),
                "numeric_columns": data.select_dtypes(include=[np.number]).columns.tolist(),
                "categorical_columns": data.select_dtypes(include=['object']).columns.tolist(),
                "date_columns": data.select_dtypes(include=['datetime64']).columns.tolist()
            }
            
            # Calcular estatísticas para colunas numéricas
            numeric_stats = {}
            for col in quality_report["numeric_columns"]:
                numeric_stats[col] = {
                    "mean": data[col].mean(),
                    "std": data[col].std(),
                    "min": data[col].min(),
                    "max": data[col].max(),
                    "median": data[col].median(),
                    "skewness": data[col].skew(),
                    "kurtosis": data[col].kurtosis()
                }
            
            quality_report["numeric_statistics"] = numeric_stats
            
            # Verificar consistência temporal
            if 'date' in data.columns:
                dates = pd.to_datetime(data['date'])
                quality_report["date_range"] = {
                    "start": dates.min().isoformat(),
                    "end": dates.max().isoformat(),
                    "span_days": (dates.max() - dates.min()).days
                }
                
                # Verificar gaps temporais
                date_diffs = dates.diff().dropna()
                quality_report["temporal_gaps"] = {
                    "avg_gap_days": date_diffs.mean().days,
                    "max_gap_days": date_diffs.max().days,
                    "min_gap_days": date_diffs.min().days
                }
            
            return quality_report
            
        except Exception as e:
            raise DataError(f"Erro na validação de qualidade: {str(e)}")
    
    async def prepare_for_modeling(self, data: pd.DataFrame, 
                                 target_column: str = 'selic_move',
                                 feature_columns: list = None) -> Tuple[pd.DataFrame, pd.Series]:
        """Preparar dados para modelagem"""
        try:
            # Verificar se a coluna target existe
            if target_column not in data.columns:
                raise DataError(f"Coluna target '{target_column}' não encontrada")
            
            # Definir features
            if feature_columns is None:
                # Usar todas as colunas numéricas exceto target
                numeric_columns = data.select_dtypes(include=[np.number]).columns
                feature_columns = [col for col in numeric_columns if col != target_column]
            
            # Verificar se as features existem
            missing_features = [col for col in feature_columns if col not in data.columns]
            if missing_features:
                raise DataError(f"Features não encontradas: {missing_features}")
            
            # Separar features e target
            X = data[feature_columns].copy()
            y = data[target_column].copy()
            
            # Remover linhas com NaN
            valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
            X = X[valid_mask]
            y = y[valid_mask]
            
            if len(X) == 0:
                raise DataError("Nenhum dado válido após limpeza")
            
            return X, y
            
        except Exception as e:
            raise DataError(f"Erro na preparação para modelagem: {str(e)}")
