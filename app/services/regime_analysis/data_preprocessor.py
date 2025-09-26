"""
Pré-processador de Dados para Análise de Regimes
Implementa limpeza, normalização e validação de dados econômicos
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import KNNImputer
import warnings
warnings.filterwarnings('ignore')

from .interfaces import IDataPreprocessor

logger = logging.getLogger(__name__)


class ScientificDataPreprocessor(IDataPreprocessor):
    """
    Pré-processador científico para dados econômicos
    Implementa limpeza e validação robusta
    """
    
    def __init__(self, 
                 outlier_method: str = 'iqr',
                 imputation_method: str = 'knn',
                 scaling_method: str = 'robust'):
        """
        Inicializa o pré-processador
        
        Args:
            outlier_method: Método para detecção de outliers ('iqr', 'zscore', 'isolation')
            imputation_method: Método para imputação ('knn', 'linear', 'forward_fill')
            scaling_method: Método de normalização ('robust', 'standard', 'minmax')
        """
        self.outlier_method = outlier_method
        self.imputation_method = imputation_method
        self.scaling_method = scaling_method
        
        # Inicializar scalers
        if scaling_method == 'robust':
            self.scaler = RobustScaler()
        elif scaling_method == 'standard':
            self.scaler = StandardScaler()
        else:
            self.scaler = StandardScaler()
        
        # Inicializar imputer
        if imputation_method == 'knn':
            self.imputer = KNNImputer(n_neighbors=5)
        else:
            self.imputer = None
    
    async def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara dados para análise de regimes
        
        Args:
            data: DataFrame com dados econômicos brutos
            
        Returns:
            DataFrame pré-processado
        """
        try:
            logger.info("🔧 Iniciando pré-processamento de dados")
            logger.info(f"📊 Dados originais: {data.shape}")
            
            # 1. Validação inicial
            validated_data = await self._validate_input_data(data)
            if validated_data is None:
                raise ValueError("Dados de entrada inválidos")
            
            # 2. Limpeza de dados
            cleaned_data = await self._clean_data(validated_data)
            logger.info(f"🧹 Dados limpos: {cleaned_data.shape}")
            
            # 3. Detecção e tratamento de outliers
            outlier_treated_data = await self._treat_outliers(cleaned_data)
            logger.info(f"🎯 Outliers tratados: {outlier_treated_data.shape}")
            
            # 4. Imputação de valores faltantes
            imputed_data = await self._impute_missing_values(outlier_treated_data)
            logger.info(f"🔧 Valores faltantes imputados: {imputed_data.shape}")
            
            # 5. Normalização
            normalized_data = await self._normalize_data(imputed_data)
            logger.info(f"📏 Dados normalizados: {normalized_data.shape}")
            
            # 6. Validação final
            final_data = await self._validate_processed_data(normalized_data)
            logger.info(f"✅ Pré-processamento concluído: {final_data.shape}")
            
            return final_data
            
        except Exception as e:
            logger.error(f"❌ Erro no pré-processamento: {e}")
            raise
    
    async def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Valida qualidade dos dados
        
        Args:
            data: DataFrame para validação
            
        Returns:
            Dicionário com métricas de qualidade
        """
        try:
            logger.info("🔍 Validando qualidade dos dados")
            
            quality_metrics = {}
            
            # 1. Completude
            completeness = await self._calculate_completeness(data)
            quality_metrics['completeness'] = completeness
            
            # 2. Consistência temporal
            temporal_consistency = await self._calculate_temporal_consistency(data)
            quality_metrics['temporal_consistency'] = temporal_consistency
            
            # 3. Variabilidade
            variability = await self._calculate_variability(data)
            quality_metrics['variability'] = variability
            
            # 4. Estacionariedade
            stationarity = await self._calculate_stationarity(data)
            quality_metrics['stationarity'] = stationarity
            
            # 5. Qualidade geral
            overall_quality = np.mean(list(quality_metrics.values()))
            quality_metrics['overall_quality'] = overall_quality
            
            # 6. Classificação da qualidade
            if overall_quality >= 0.9:
                quality_level = 'excellent'
            elif overall_quality >= 0.7:
                quality_level = 'good'
            elif overall_quality >= 0.5:
                quality_level = 'fair'
            else:
                quality_level = 'poor'
            
            quality_metrics['quality_level'] = quality_level
            
            logger.info(f"📊 Qualidade geral: {overall_quality:.2f} ({quality_level})")
            return quality_metrics
            
        except Exception as e:
            logger.error(f"❌ Erro na validação de qualidade: {e}")
            return {'error': str(e)}
    
    async def _validate_input_data(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Valida dados de entrada"""
        try:
            if data is None or data.empty:
                logger.error("❌ Dados vazios ou nulos")
                return None
            
            if len(data) < 10:
                logger.error("❌ Dados insuficientes (mínimo 10 observações)")
                return None
            
            # Verificar se há colunas numéricas
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) == 0:
                logger.error("❌ Nenhuma coluna numérica encontrada")
                return None
            
            logger.info(f"✅ Dados válidos: {len(data)} observações, {len(numeric_columns)} colunas numéricas")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro na validação de entrada: {e}")
            return None
    
    async def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados básicos"""
        try:
            cleaned_data = data.copy()
            
            # Remover colunas completamente vazias
            cleaned_data = cleaned_data.dropna(axis=1, how='all')
            
            # Converter colunas de data
            if 'date' in cleaned_data.columns:
                cleaned_data['date'] = pd.to_datetime(cleaned_data['date'], errors='coerce')
            
            # Remover linhas com todas as colunas numéricas nulas
            numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns
            cleaned_data = cleaned_data.dropna(subset=numeric_columns, how='all')
            
            # Ordenar por data se disponível
            if 'date' in cleaned_data.columns:
                cleaned_data = cleaned_data.sort_values('date').reset_index(drop=True)
            
            logger.info(f"🧹 Dados limpos: {cleaned_data.shape}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
            return data
    
    async def _treat_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Trata outliers nos dados"""
        try:
            treated_data = data.copy()
            numeric_columns = treated_data.select_dtypes(include=[np.number]).columns
            
            for column in numeric_columns:
                if column == 'date':
                    continue
                
                if self.outlier_method == 'iqr':
                    treated_data[column] = self._treat_outliers_iqr(treated_data[column])
                elif self.outlier_method == 'zscore':
                    treated_data[column] = self._treat_outliers_zscore(treated_data[column])
                elif self.outlier_method == 'isolation':
                    treated_data[column] = await self._treat_outliers_isolation(treated_data[column])
            
            logger.info(f"🎯 Outliers tratados usando método: {self.outlier_method}")
            return treated_data
            
        except Exception as e:
            logger.error(f"❌ Erro no tratamento de outliers: {e}")
            return data
    
    def _treat_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """Trata outliers usando método IQR"""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            return series.clip(lower_bound, upper_bound)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro no tratamento IQR: {e}")
            return series
    
    def _treat_outliers_zscore(self, series: pd.Series) -> pd.Series:
        """Trata outliers usando método Z-score"""
        try:
            z_scores = np.abs((series - series.mean()) / series.std())
            threshold = 3.0
            
            return series.where(z_scores <= threshold, series.median())
            
        except Exception as e:
            logger.warning(f"⚠️ Erro no tratamento Z-score: {e}")
            return series
    
    async def _treat_outliers_isolation(self, series: pd.Series) -> pd.Series:
        """Trata outliers usando Isolation Forest"""
        try:
            from sklearn.ensemble import IsolationForest
            
            # Reshape para 2D
            X = series.values.reshape(-1, 1)
            
            # Aplicar Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outlier_mask = iso_forest.fit_predict(X) == -1
            
            # Substituir outliers pela mediana
            series_clean = series.copy()
            series_clean[outlier_mask] = series.median()
            
            return series_clean
            
        except Exception as e:
            logger.warning(f"⚠️ Erro no Isolation Forest: {e}")
            return series
    
    async def _impute_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Imputa valores faltantes"""
        try:
            imputed_data = data.copy()
            numeric_columns = imputed_data.select_dtypes(include=[np.number]).columns
            
            if self.imputation_method == 'knn' and self.imputer is not None:
                # Usar KNN imputer
                imputed_data[numeric_columns] = self.imputer.fit_transform(imputed_data[numeric_columns])
            elif self.imputation_method == 'linear':
                # Interpolação linear
                imputed_data[numeric_columns] = imputed_data[numeric_columns].interpolate(method='linear')
            else:
                # Forward fill + backward fill
                imputed_data[numeric_columns] = imputed_data[numeric_columns].fillna(method='ffill').fillna(method='bfill')
            
            logger.info(f"🔧 Valores faltantes imputados usando: {self.imputation_method}")
            return imputed_data
            
        except Exception as e:
            logger.error(f"❌ Erro na imputação: {e}")
            return data
    
    async def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normaliza dados"""
        try:
            normalized_data = data.copy()
            numeric_columns = normalized_data.select_dtypes(include=[np.number]).columns
            
            # Normalizar apenas colunas numéricas (exceto date)
            numeric_columns = [col for col in numeric_columns if col != 'date']
            
            if len(numeric_columns) > 0:
                normalized_data[numeric_columns] = self.scaler.fit_transform(normalized_data[numeric_columns])
            
            logger.info(f"📏 Dados normalizados usando: {self.scaling_method}")
            return normalized_data
            
        except Exception as e:
            logger.error(f"❌ Erro na normalização: {e}")
            return data
    
    async def _validate_processed_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Valida dados processados"""
        try:
            # Verificar se ainda há dados
            if data.empty:
                raise ValueError("Dados vazios após processamento")
            
            # Verificar se há valores infinitos
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            inf_count = np.isinf(data[numeric_columns]).sum().sum()
            
            if inf_count > 0:
                logger.warning(f"⚠️ {inf_count} valores infinitos encontrados, substituindo por NaN")
                data[numeric_columns] = data[numeric_columns].replace([np.inf, -np.inf], np.nan)
                data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].median())
            
            # Verificar se há valores NaN
            nan_count = data[numeric_columns].isnull().sum().sum()
            if nan_count > 0:
                logger.warning(f"⚠️ {nan_count} valores NaN encontrados após processamento")
            
            logger.info("✅ Dados processados validados")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro na validação final: {e}")
            raise
    
    async def _calculate_completeness(self, data: pd.DataFrame) -> float:
        """Calcula completude dos dados"""
        try:
            total_values = data.size
            missing_values = data.isnull().sum().sum()
            completeness = 1.0 - (missing_values / total_values)
            
            return float(completeness)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular completude: {e}")
            return 0.0
    
    async def _calculate_temporal_consistency(self, data: pd.DataFrame) -> float:
        """Calcula consistência temporal"""
        try:
            if 'date' not in data.columns:
                return 1.0  # Sem coluna de data, assumir consistente
            
            # Verificar gaps temporais
            date_series = pd.to_datetime(data['date'], errors='coerce')
            date_gaps = date_series.diff().dt.days
            
            # Calcular consistência baseada em gaps
            expected_gap = date_gaps.mode().iloc[0] if not date_gaps.empty else 30
            gap_consistency = 1.0 - (date_gaps.isnull().sum() / len(date_gaps))
            
            # Penalizar gaps muito grandes
            large_gaps = (date_gaps > expected_gap * 2).sum()
            gap_penalty = large_gaps / len(date_gaps)
            
            consistency = gap_consistency - gap_penalty
            return float(max(0.0, consistency))
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular consistência temporal: {e}")
            return 0.0
    
    async def _calculate_variability(self, data: pd.DataFrame) -> float:
        """Calcula variabilidade dos dados"""
        try:
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) == 0:
                return 0.0
            
            # Calcular coeficiente de variação para cada coluna
            cv_scores = []
            for column in numeric_columns:
                if column == 'date':
                    continue
                
                series = data[column].dropna()
                if len(series) > 1 and series.std() > 0:
                    cv = series.std() / abs(series.mean())
                    cv_scores.append(cv)
            
            if not cv_scores:
                return 0.0
            
            # Variabilidade média (normalizada)
            avg_cv = np.mean(cv_scores)
            variability = min(avg_cv / 2.0, 1.0)  # Normalizar para 0-1
            
            return float(variability)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular variabilidade: {e}")
            return 0.0
    
    async def _calculate_stationarity(self, data: pd.DataFrame) -> float:
        """Calcula estacionariedade dos dados"""
        try:
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) == 0:
                return 0.0
            
            # Teste simples de estacionariedade baseado em tendência
            stationarity_scores = []
            
            for column in numeric_columns:
                if column == 'date':
                    continue
                
                series = data[column].dropna()
                if len(series) < 10:
                    continue
                
                # Calcular correlação com tempo (proxy para tendência)
                time_corr = abs(np.corrcoef(range(len(series)), series)[0, 1])
                
                # Estacionariedade inversamente relacionada à correlação temporal
                stationarity = 1.0 - time_corr
                stationarity_scores.append(stationarity)
            
            if not stationarity_scores:
                return 0.0
            
            return float(np.mean(stationarity_scores))
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular estacionariedade: {e}")
            return 0.0
