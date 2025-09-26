"""
Validador de Dados Robusto
Conforme DRS seção 7.3 - Validação e Limpeza
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """Problema de validação identificado"""
    level: str  # 'error', 'warning', 'info'
    column: str
    message: str
    affected_rows: List[int]
    suggested_fix: Optional[str] = None

@dataclass
class ValidationResult:
    """Resultado da validação de dados"""
    is_valid: bool
    issues: List[ValidationIssue]
    quality_score: float
    data_summary: Dict[str, Any]

class DataValidator:
    """
    Validador robusto de dados econômicos
    
    Implementa validação conforme DRS seção 7.3
    """
    
    def __init__(self):
        """Inicializar validador de dados"""
        self.validation_rules = {
            'gdp_growth': {'min': -20.0, 'max': 20.0},
            'inflation': {'min': -5.0, 'max': 50.0},
            'unemployment': {'min': 0.0, 'max': 30.0},
            'policy_rate': {'min': -2.0, 'max': 25.0},
            'vix': {'min': 5.0, 'max': 100.0},
            'exchange_rate': {'min': 0.1, 'max': 1000.0}
        }
        
        self.outlier_methods = ['iqr', 'zscore', 'modified_zscore']
    
    def validate_dataset(
        self, 
        data: pd.DataFrame, 
        source: str
    ) -> ValidationResult:
        """
        Validar dataset completo
        
        Args:
            data: DataFrame com dados
            source: Fonte dos dados ('fred', 'bcb', 'oecd', etc.)
            
        Returns:
            ValidationResult: Resultado da validação
        """
        logger.info(f"Validando dataset de {source}")
        
        issues = []
        quality_scores = []
        
        # 1. Validação estrutural
        structural_issues = self._validate_structure(data)
        issues.extend(structural_issues)
        
        # 2. Validação de valores
        value_issues = self._validate_values(data)
        issues.extend(value_issues)
        
        # 3. Validação temporal
        temporal_issues = self._validate_temporal_consistency(data)
        issues.extend(temporal_issues)
        
        # 4. Validação de outliers
        outlier_issues = self._detect_outliers(data)
        issues.extend(outlier_issues)
        
        # 5. Validação de dados faltantes
        missing_issues = self._validate_missing_data(data)
        issues.extend(missing_issues)
        
        # 6. Calcular score de qualidade
        quality_score = self._calculate_quality_score(data, issues)
        
        # 7. Gerar resumo dos dados
        data_summary = self._generate_data_summary(data)
        
        # 8. Determinar se dados são válidos
        is_valid = self._determine_validity(issues, quality_score)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            quality_score=quality_score,
            data_summary=data_summary
        )
    
    def _validate_structure(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Validar estrutura dos dados"""
        issues = []
        
        # Verificar se DataFrame não está vazio
        if data.empty:
            issues.append(ValidationIssue(
                level='error',
                column='all',
                message='Dataset está vazio',
                affected_rows=[],
                suggested_fix='Verificar fonte de dados'
            ))
            return issues
        
        # Verificar se há colunas
        if len(data.columns) == 0:
            issues.append(ValidationIssue(
                level='error',
                column='all',
                message='Dataset não possui colunas',
                affected_rows=[],
                suggested_fix='Verificar estrutura dos dados'
            ))
            return issues
        
        # Verificar se há índice temporal
        if not isinstance(data.index, pd.DatetimeIndex):
            issues.append(ValidationIssue(
                level='warning',
                column='index',
                message='Índice não é temporal',
                affected_rows=[],
                suggested_fix='Converter índice para datetime'
            ))
        
        return issues
    
    def _validate_values(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Validar valores dos dados"""
        issues = []
        
        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column].dropna()
            
            if len(series) == 0:
                continue
            
            # Verificar valores infinitos
            inf_count = np.isinf(series).sum()
            if inf_count > 0:
                issues.append(ValidationIssue(
                    level='error',
                    column=column,
                    message=f'Encontrados {inf_count} valores infinitos',
                    affected_rows=series[np.isinf(series)].index.tolist(),
                    suggested_fix='Remover ou substituir valores infinitos'
                ))
            
            # Verificar valores NaN
            nan_count = series.isna().sum()
            if nan_count > 0:
                issues.append(ValidationIssue(
                    level='warning',
                    column=column,
                    message=f'Encontrados {nan_count} valores NaN',
                    affected_rows=series[series.isna()].index.tolist(),
                    suggested_fix='Tratar valores faltantes'
                ))
            
            # Verificar regras específicas por tipo de indicador
            if column.lower() in self.validation_rules:
                rules = self.validation_rules[column.lower()]
                
                # Verificar valores mínimos
                below_min = series < rules['min']
                if below_min.any():
                    issues.append(ValidationIssue(
                        level='warning',
                        column=column,
                        message=f'Valores abaixo do mínimo esperado ({rules["min"]})',
                        affected_rows=series[below_min].index.tolist(),
                        suggested_fix='Verificar se valores estão corretos'
                    ))
                
                # Verificar valores máximos
                above_max = series > rules['max']
                if above_max.any():
                    issues.append(ValidationIssue(
                        level='warning',
                        column=column,
                        message=f'Valores acima do máximo esperado ({rules["max"]})',
                        affected_rows=series[above_max].index.tolist(),
                        suggested_fix='Verificar se valores estão corretos'
                    ))
        
        return issues
    
    def _validate_temporal_consistency(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Validar consistência temporal"""
        issues = []
        
        if not isinstance(data.index, pd.DatetimeIndex):
            return issues
        
        # Verificar se há gaps temporais grandes
        time_diffs = data.index.to_series().diff()
        median_diff = time_diffs.median()
        
        # Identificar gaps maiores que 3x a mediana
        large_gaps = time_diffs > (3 * median_diff)
        if large_gaps.any():
            issues.append(ValidationIssue(
                level='warning',
                column='index',
                message=f'Encontrados {large_gaps.sum()} gaps temporais grandes',
                affected_rows=data.index[large_gaps].tolist(),
                suggested_fix='Verificar se há dados faltantes'
            ))
        
        # Verificar se há duplicatas temporais
        duplicates = data.index.duplicated()
        if duplicates.any():
            issues.append(ValidationIssue(
                level='error',
                column='index',
                message=f'Encontradas {duplicates.sum()} datas duplicadas',
                affected_rows=data.index[duplicates].tolist(),
                suggested_fix='Remover duplicatas temporais'
            ))
        
        return issues
    
    def _detect_outliers(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Detectar outliers usando múltiplos métodos"""
        issues = []
        
        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column].dropna()
            
            if len(series) < 10:  # Muito poucos dados para detectar outliers
                continue
            
            outlier_indices = set()
            
            # Método 1: IQR
            iqr_outliers = self._detect_outliers_iqr(series)
            outlier_indices.update(iqr_outliers)
            
            # Método 2: Z-Score modificado
            zscore_outliers = self._detect_outliers_zscore(series)
            outlier_indices.update(zscore_outliers)
            
            # Método 3: Z-Score modificado (mais robusto)
            modified_zscore_outliers = self._detect_outliers_modified_zscore(series)
            outlier_indices.update(modified_zscore_outliers)
            
            if outlier_indices:
                issues.append(ValidationIssue(
                    level='warning',
                    column=column,
                    message=f'Detectados {len(outlier_indices)} outliers',
                    affected_rows=list(outlier_indices),
                    suggested_fix='Verificar se outliers são legítimos ou erros'
                ))
        
        return issues
    
    def _detect_outliers_iqr(self, series: pd.Series) -> List[int]:
        """Detectar outliers usando método IQR"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return outliers.index.tolist()
    
    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> List[int]:
        """Detectar outliers usando Z-Score"""
        z_scores = np.abs((series - series.mean()) / series.std())
        outliers = series[z_scores > threshold]
        return outliers.index.tolist()
    
    def _detect_outliers_modified_zscore(self, series: pd.Series, threshold: float = 3.5) -> List[int]:
        """Detectar outliers usando Z-Score modificado (mais robusto)"""
        median = series.median()
        mad = np.median(np.abs(series - median))
        modified_z_scores = 0.6745 * (series - median) / mad
        outliers = series[np.abs(modified_z_scores) > threshold]
        return outliers.index.tolist()
    
    def _validate_missing_data(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Validar dados faltantes"""
        issues = []
        
        for column in data.columns:
            missing_count = data[column].isna().sum()
            missing_pct = missing_count / len(data) * 100
            
            if missing_pct > 10:  # Mais de 10% faltante
                issues.append(ValidationIssue(
                    level='error',
                    column=column,
                    message=f'{missing_pct:.1f}% de dados faltantes',
                    affected_rows=data[data[column].isna()].index.tolist(),
                    suggested_fix='Implementar estratégia de imputação'
                ))
            elif missing_pct > 5:  # Mais de 5% faltante
                issues.append(ValidationIssue(
                    level='warning',
                    column=column,
                    message=f'{missing_pct:.1f}% de dados faltantes',
                    affected_rows=data[data[column].isna()].index.tolist(),
                    suggested_fix='Considerar estratégia de imputação'
                ))
        
        return issues
    
    def _calculate_quality_score(
        self, 
        data: pd.DataFrame, 
        issues: List[ValidationIssue]
    ) -> float:
        """Calcular score de qualidade dos dados"""
        
        if data.empty:
            return 0.0
        
        # Score base
        base_score = 1.0
        
        # Penalizar por problemas
        error_penalty = sum(1 for issue in issues if issue.level == 'error') * 0.2
        warning_penalty = sum(1 for issue in issues if issue.level == 'warning') * 0.1
        
        # Penalizar por dados faltantes
        missing_penalty = data.isna().sum().sum() / (len(data) * len(data.columns)) * 0.3
        
        # Calcular score final
        quality_score = max(0.0, base_score - error_penalty - warning_penalty - missing_penalty)
        
        return quality_score
    
    def _generate_data_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Gerar resumo dos dados"""
        summary = {
            'shape': data.shape,
            'columns': list(data.columns),
            'dtypes': data.dtypes.to_dict(),
            'memory_usage': data.memory_usage(deep=True).sum(),
            'date_range': {
                'start': data.index.min() if isinstance(data.index, pd.DatetimeIndex) else None,
                'end': data.index.max() if isinstance(data.index, pd.DatetimeIndex) else None
            }
        }
        
        # Estatísticas descritivas
        if len(data.select_dtypes(include=[np.number]).columns) > 0:
            summary['descriptive_stats'] = data.describe().to_dict()
        
        return summary
    
    def _determine_validity(
        self, 
        issues: List[ValidationIssue], 
        quality_score: float
    ) -> bool:
        """Determinar se os dados são válidos"""
        
        # Dados são inválidos se:
        # 1. Há erros críticos
        has_errors = any(issue.level == 'error' for issue in issues)
        
        # 2. Score de qualidade muito baixo
        low_quality = quality_score < 0.5
        
        return not (has_errors or low_quality)
