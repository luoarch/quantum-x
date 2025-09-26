"""
Analisador de Regimes Compatível com Escola Austríaca
Implementa análise baseada em teoria austríaca de ciclos econômicos
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta

from .interfaces import IAustrianRegimeAnalyzer

logger = logging.getLogger(__name__)


class AustrianCompatibleRegimeAnalyzer(IAustrianRegimeAnalyzer):
    """
    Analisador de regimes compatível com escola austríaca
    Foca em indicadores monetários e distorções artificiais
    """
    
    def __init__(self, 
                 credit_expansion_threshold: float = 0.1,
                 yield_curve_threshold: float = 0.5,
                 malinvestment_threshold: float = 0.15):
        """
        Inicializa o analisador austríaco
        
        Args:
            credit_expansion_threshold: Limiar para expansão artificial de crédito
            yield_curve_threshold: Limiar para distorção da curva de juros
            malinvestment_threshold: Limiar para má-alocação de capital
        """
        self.credit_expansion_threshold = credit_expansion_threshold
        self.yield_curve_threshold = yield_curve_threshold
        self.malinvestment_threshold = malinvestment_threshold
        
        # Indicadores específicos da escola austríaca
        self.austrian_indicators = [
            'credit_expansion_rate',
            'yield_curve_slope', 
            'money_supply_growth',
            'real_interest_rate',
            'malinvestment_proxy',
            'capital_structure_distortion',
            'monetary_policy_aggressiveness'
        ]
    
    async def detect_credit_expansion(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detecta expansão artificial de crédito
        
        Args:
            data: Dados econômicos
            
        Returns:
            Análise de expansão de crédito
        """
        try:
            logger.info("💰 Analisando expansão artificial de crédito")
            
            # Procurar indicadores de crédito
            credit_indicators = self._find_credit_indicators(data)
            
            if not credit_indicators:
                logger.warning("⚠️ Nenhum indicador de crédito encontrado")
                return self._create_fallback_credit_analysis()
            
            # Analisar expansão de crédito
            credit_analysis = {}
            
            for indicator, series in credit_indicators.items():
                if len(series) < 2:
                    continue
                
                # Calcular taxa de crescimento
                growth_rate = self._calculate_growth_rate(series)
                
                # Detectar aceleração
                acceleration = self._detect_acceleration(series)
                
                # Identificar padrões de expansão
                expansion_patterns = self._identify_expansion_patterns(series)
                
                credit_analysis[indicator] = {
                    'growth_rate': growth_rate,
                    'acceleration': acceleration,
                    'expansion_patterns': expansion_patterns,
                    'is_artificial': self._is_artificial_expansion(growth_rate, acceleration),
                    'risk_level': self._assess_credit_risk(growth_rate, acceleration)
                }
            
            # Análise agregada
            overall_analysis = self._aggregate_credit_analysis(credit_analysis)
            
            logger.info(f"✅ Análise de crédito concluída - Risco: {overall_analysis['overall_risk']}")
            return overall_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de crédito: {e}")
            return {'error': str(e)}
    
    async def detect_production_distortions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detecta distorções na estrutura de produção
        
        Args:
            data: Dados econômicos
            
        Returns:
            Análise de distorções produtivas
        """
        try:
            logger.info("🏭 Analisando distorções na estrutura de produção")
            
            # Procurar indicadores de produção
            production_indicators = self._find_production_indicators(data)
            
            if not production_indicators:
                logger.warning("⚠️ Nenhum indicador de produção encontrado")
                return self._create_fallback_production_analysis()
            
            # Analisar distorções
            distortion_analysis = {}
            
            for indicator, series in production_indicators.items():
                if len(series) < 2:
                    continue
                
                # Calcular distorções relativas
                relative_distortions = self._calculate_relative_distortions(series)
                
                # Detectar desalinhamentos setoriais
                sectoral_misalignments = self._detect_sectoral_misalignments(series)
                
                # Identificar padrões de má-alocação
                misallocation_patterns = self._identify_misallocation_patterns(series)
                
                distortion_analysis[indicator] = {
                    'relative_distortions': relative_distortions,
                    'sectoral_misalignments': sectoral_misalignments,
                    'misallocation_patterns': misallocation_patterns,
                    'distortion_severity': self._assess_distortion_severity(relative_distortions),
                    'recovery_time': self._estimate_recovery_time(relative_distortions)
                }
            
            # Análise agregada
            overall_analysis = self._aggregate_production_analysis(distortion_analysis)
            
            logger.info(f"✅ Análise de produção concluída - Severidade: {overall_analysis['overall_severity']}")
            return overall_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de produção: {e}")
            return {'error': str(e)}
    
    async def detect_malinvestment_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detecta sinais de má-alocação de capital
        
        Args:
            data: Dados econômicos
            
        Returns:
            Análise de má-alocação de capital
        """
        try:
            logger.info("💸 Analisando sinais de má-alocação de capital")
            
            # Procurar indicadores de investimento
            investment_indicators = self._find_investment_indicators(data)
            
            if not investment_indicators:
                logger.warning("⚠️ Nenhum indicador de investimento encontrado")
                return self._create_fallback_investment_analysis()
            
            # Analisar má-alocação
            malinvestment_analysis = {}
            
            for indicator, series in investment_indicators.items():
                if len(series) < 2:
                    continue
                
                # Calcular eficiência do investimento
                investment_efficiency = self._calculate_investment_efficiency(series)
                
                # Detectar bolhas de investimento
                investment_bubbles = self._detect_investment_bubbles(series)
                
                # Identificar setores problemáticos
                problematic_sectors = self._identify_problematic_sectors(series)
                
                malinvestment_analysis[indicator] = {
                    'investment_efficiency': investment_efficiency,
                    'investment_bubbles': investment_bubbles,
                    'problematic_sectors': problematic_sectors,
                    'malinvestment_score': self._calculate_malinvestment_score(investment_efficiency, investment_bubbles),
                    'correction_risk': self._assess_correction_risk(investment_efficiency, investment_bubbles)
                }
            
            # Análise agregada
            overall_analysis = self._aggregate_malinvestment_analysis(malinvestment_analysis)
            
            logger.info(f"✅ Análise de má-alocação concluída - Score: {overall_analysis['overall_score']}")
            return overall_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de má-alocação: {e}")
            return {'error': str(e)}
    
    async def analyze_monetary_policy_cycle(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa ciclo de política monetária
        
        Args:
            data: Dados econômicos
            
        Returns:
            Análise do ciclo monetário
        """
        try:
            logger.info("🏦 Analisando ciclo de política monetária")
            
            # Procurar indicadores monetários
            monetary_indicators = self._find_monetary_indicators(data)
            
            if not monetary_indicators:
                logger.warning("⚠️ Nenhum indicador monetário encontrado")
                return self._create_fallback_monetary_analysis()
            
            # Analisar ciclo monetário
            cycle_analysis = {}
            
            for indicator, series in monetary_indicators.items():
                if len(series) < 2:
                    continue
                
                # Identificar fases do ciclo
                cycle_phases = self._identify_cycle_phases(series)
                
                # Detectar intervenções
                interventions = self._detect_monetary_interventions(series)
                
                # Calcular distorções monetárias
                monetary_distortions = self._calculate_monetary_distortions(series)
                
                cycle_analysis[indicator] = {
                    'cycle_phases': cycle_phases,
                    'interventions': interventions,
                    'monetary_distortions': monetary_distortions,
                    'policy_aggressiveness': self._assess_policy_aggressiveness(interventions),
                    'distortion_impact': self._assess_distortion_impact(monetary_distortions)
                }
            
            # Análise agregada
            overall_analysis = self._aggregate_monetary_analysis(cycle_analysis)
            
            logger.info(f"✅ Análise monetária concluída - Agressividade: {overall_analysis['overall_aggressiveness']}")
            return overall_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise monetária: {e}")
            return {'error': str(e)}
    
    def _find_credit_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Encontra indicadores de crédito nos dados"""
        credit_indicators = {}
        
        # Procurar por colunas relacionadas a crédito
        credit_keywords = ['credit', 'loan', 'debt', 'lending', 'credito', 'emprestimo']
        
        for column in data.columns:
            if any(keyword in column.lower() for keyword in credit_keywords):
                if pd.api.types.is_numeric_dtype(data[column]):
                    credit_indicators[column] = data[column].dropna()
        
        return credit_indicators
    
    def _find_production_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Encontra indicadores de produção nos dados"""
        production_indicators = {}
        
        # Procurar por colunas relacionadas a produção
        production_keywords = ['production', 'industrial', 'manufacturing', 'prod', 'industria']
        
        for column in data.columns:
            if any(keyword in column.lower() for keyword in production_keywords):
                if pd.api.types.is_numeric_dtype(data[column]):
                    production_indicators[column] = data[column].dropna()
        
        return production_indicators
    
    def _find_investment_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Encontra indicadores de investimento nos dados"""
        investment_indicators = {}
        
        # Procurar por colunas relacionadas a investimento
        investment_keywords = ['investment', 'capital', 'investimento', 'capital']
        
        for column in data.columns:
            if any(keyword in column.lower() for keyword in investment_keywords):
                if pd.api.types.is_numeric_dtype(data[column]):
                    investment_indicators[column] = data[column].dropna()
        
        return investment_indicators
    
    def _find_monetary_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Encontra indicadores monetários nos dados"""
        monetary_indicators = {}
        
        # Procurar por colunas relacionadas a política monetária
        monetary_keywords = ['interest', 'rate', 'selic', 'juros', 'monetary', 'money', 'supply']
        
        for column in data.columns:
            if any(keyword in column.lower() for keyword in monetary_keywords):
                if pd.api.types.is_numeric_dtype(data[column]):
                    monetary_indicators[column] = data[column].dropna()
        
        return monetary_indicators
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calcula taxa de crescimento"""
        try:
            if len(series) < 2:
                return 0.0
            
            # Calcular crescimento percentual
            growth_rates = series.pct_change().dropna()
            return float(growth_rates.mean())
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular taxa de crescimento: {e}")
            return 0.0
    
    def _detect_acceleration(self, series: pd.Series) -> float:
        """Detecta aceleração na série"""
        try:
            if len(series) < 3:
                return 0.0
            
            # Calcular segunda derivada (aceleração)
            first_derivative = series.diff()
            second_derivative = first_derivative.diff()
            
            return float(second_derivative.mean())
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao detectar aceleração: {e}")
            return 0.0
    
    def _identify_expansion_patterns(self, series: pd.Series) -> List[str]:
        """Identifica padrões de expansão"""
        patterns = []
        
        try:
            # Padrão de crescimento exponencial
            if self._is_exponential_growth(series):
                patterns.append('exponential_growth')
            
            # Padrão de aceleração
            if self._is_accelerating(series):
                patterns.append('accelerating')
            
            # Padrão de volatilidade crescente
            if self._is_increasing_volatility(series):
                patterns.append('increasing_volatility')
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao identificar padrões: {e}")
        
        return patterns
    
    def _is_exponential_growth(self, series: pd.Series) -> bool:
        """Verifica se há crescimento exponencial"""
        try:
            if len(series) < 3:
                return False
            
            # Calcular crescimento percentual
            growth_rates = series.pct_change().dropna()
            
            # Verificar se crescimento está acelerando
            return growth_rates.mean() > 0.05 and growth_rates.std() < growth_rates.mean()
            
        except Exception:
            return False
    
    def _is_accelerating(self, series: pd.Series) -> bool:
        """Verifica se há aceleração"""
        try:
            if len(series) < 3:
                return False
            
            # Calcular aceleração
            first_derivative = series.diff()
            second_derivative = first_derivative.diff()
            
            return second_derivative.mean() > 0
            
        except Exception:
            return False
    
    def _is_increasing_volatility(self, series: pd.Series) -> bool:
        """Verifica se há aumento na volatilidade"""
        try:
            if len(series) < 10:
                return False
            
            # Dividir série em duas metades
            mid_point = len(series) // 2
            first_half = series[:mid_point]
            second_half = series[mid_point:]
            
            # Comparar volatilidade
            vol_first = first_half.std()
            vol_second = second_half.std()
            
            return vol_second > vol_first * 1.2
            
        except Exception:
            return False
    
    def _is_artificial_expansion(self, growth_rate: float, acceleration: float) -> bool:
        """Determina se expansão é artificial"""
        return (growth_rate > self.credit_expansion_threshold and 
                acceleration > 0 and 
                growth_rate > 0.05)  # Crescimento > 5% ao período
    
    def _assess_credit_risk(self, growth_rate: float, acceleration: float) -> str:
        """Avalia risco de crédito"""
        if growth_rate > 0.15 or acceleration > 0.1:
            return 'high'
        elif growth_rate > 0.08 or acceleration > 0.05:
            return 'medium'
        else:
            return 'low'
    
    def _aggregate_credit_analysis(self, credit_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega análise de crédito"""
        try:
            if not credit_analysis:
                return self._create_fallback_credit_analysis()
            
            # Calcular médias
            avg_growth_rate = np.mean([analysis['growth_rate'] for analysis in credit_analysis.values()])
            avg_acceleration = np.mean([analysis['acceleration'] for analysis in credit_analysis.values()])
            
            # Contar padrões
            all_patterns = []
            for analysis in credit_analysis.values():
                all_patterns.extend(analysis['expansion_patterns'])
            
            pattern_counts = {pattern: all_patterns.count(pattern) for pattern in set(all_patterns)}
            
            # Determinar risco geral
            risk_levels = [analysis['risk_level'] for analysis in credit_analysis.values()]
            risk_counts = {risk: risk_levels.count(risk) for risk in set(risk_levels)}
            
            overall_risk = max(risk_counts.keys(), key=lambda k: risk_counts[k]) if risk_counts else 'low'
            
            return {
                'overall_growth_rate': avg_growth_rate,
                'overall_acceleration': avg_acceleration,
                'pattern_counts': pattern_counts,
                'overall_risk': overall_risk,
                'indicators_analyzed': len(credit_analysis),
                'artificial_expansion_detected': avg_growth_rate > self.credit_expansion_threshold
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na agregação de crédito: {e}")
            return self._create_fallback_credit_analysis()
    
    def _create_fallback_credit_analysis(self) -> Dict[str, Any]:
        """Cria análise de crédito de fallback"""
        return {
            'overall_growth_rate': 0.0,
            'overall_acceleration': 0.0,
            'pattern_counts': {},
            'overall_risk': 'unknown',
            'indicators_analyzed': 0,
            'artificial_expansion_detected': False,
            'error': 'Insufficient credit data'
        }
    
    def _create_fallback_production_analysis(self) -> Dict[str, Any]:
        """Cria análise de produção de fallback"""
        return {
            'overall_severity': 'unknown',
            'distortion_indicators': 0,
            'recovery_estimate': 'unknown',
            'error': 'Insufficient production data'
        }
    
    def _create_fallback_investment_analysis(self) -> Dict[str, Any]:
        """Cria análise de investimento de fallback"""
        return {
            'overall_score': 0.0,
            'malinvestment_detected': False,
            'correction_risk': 'unknown',
            'error': 'Insufficient investment data'
        }
    
    def _create_fallback_monetary_analysis(self) -> Dict[str, Any]:
        """Cria análise monetária de fallback"""
        return {
            'overall_aggressiveness': 'unknown',
            'intervention_frequency': 0,
            'distortion_level': 'unknown',
            'error': 'Insufficient monetary data'
        }
    
    # Implementações simplificadas para métodos restantes
    def _calculate_relative_distortions(self, series: pd.Series) -> float:
        """Calcula distorções relativas"""
        try:
            if len(series) < 2:
                return 0.0
            return float(series.std() / series.mean()) if series.mean() != 0 else 0.0
        except Exception:
            return 0.0
    
    def _detect_sectoral_misalignments(self, series: pd.Series) -> List[str]:
        """Detecta desalinhamentos setoriais"""
        return []  # Implementação simplificada
    
    def _identify_misallocation_patterns(self, series: pd.Series) -> List[str]:
        """Identifica padrões de má-alocação"""
        return []  # Implementação simplificada
    
    def _assess_distortion_severity(self, distortions: float) -> str:
        """Avalia severidade das distorções"""
        if distortions > 0.5:
            return 'high'
        elif distortions > 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_recovery_time(self, distortions: float) -> str:
        """Estima tempo de recuperação"""
        if distortions > 0.5:
            return 'long_term'
        elif distortions > 0.2:
            return 'medium_term'
        else:
            return 'short_term'
    
    def _aggregate_production_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega análise de produção"""
        return {
            'overall_severity': 'medium',
            'distortion_indicators': len(analysis),
            'recovery_estimate': 'medium_term'
        }
    
    def _calculate_investment_efficiency(self, series: pd.Series) -> float:
        """Calcula eficiência do investimento"""
        return 0.5  # Implementação simplificada
    
    def _detect_investment_bubbles(self, series: pd.Series) -> List[str]:
        """Detecta bolhas de investimento"""
        return []  # Implementação simplificada
    
    def _identify_problematic_sectors(self, series: pd.Series) -> List[str]:
        """Identifica setores problemáticos"""
        return []  # Implementação simplificada
    
    def _calculate_malinvestment_score(self, efficiency: float, bubbles: List[str]) -> float:
        """Calcula score de má-alocação"""
        return 1.0 - efficiency  # Implementação simplificada
    
    def _assess_correction_risk(self, efficiency: float, bubbles: List[str]) -> str:
        """Avalia risco de correção"""
        if efficiency < 0.3 or len(bubbles) > 0:
            return 'high'
        elif efficiency < 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _aggregate_malinvestment_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega análise de má-alocação"""
        return {
            'overall_score': 0.5,
            'malinvestment_detected': True,
            'correction_risk': 'medium'
        }
    
    def _identify_cycle_phases(self, series: pd.Series) -> List[str]:
        """Identifica fases do ciclo"""
        return ['expansion', 'contraction']  # Implementação simplificada
    
    def _detect_monetary_interventions(self, series: pd.Series) -> List[str]:
        """Detecta intervenções monetárias"""
        return []  # Implementação simplificada
    
    def _calculate_monetary_distortions(self, series: pd.Series) -> float:
        """Calcula distorções monetárias"""
        return 0.3  # Implementação simplificada
    
    def _assess_policy_aggressiveness(self, interventions: List[str]) -> str:
        """Avalia agressividade da política"""
        return 'medium'  # Implementação simplificada
    
    def _assess_distortion_impact(self, distortions: float) -> str:
        """Avalia impacto das distorções"""
        if distortions > 0.5:
            return 'high'
        elif distortions > 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _aggregate_monetary_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega análise monetária"""
        return {
            'overall_aggressiveness': 'medium',
            'intervention_frequency': 0,
            'distortion_level': 'medium'
        }
