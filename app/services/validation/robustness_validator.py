"""
Validador de Critérios de Robustez
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RobustnessLevel(Enum):
    """Níveis de robustez"""
    FAILED = "FAILED"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    EXCELLENT = "EXCELLENT"


@dataclass
class RobustnessCriteria:
    """Critérios de robustez"""
    min_sharpe_ratio: float = 1.0
    max_drawdown: float = 0.20
    min_profit_factor: float = 1.5
    min_win_rate: float = 0.55
    min_trades: int = 100
    min_consistency_score: float = 0.7
    max_volatility: float = 0.30
    min_calmar_ratio: float = 0.5


@dataclass
class RobustnessResult:
    """Resultado da validação de robustez"""
    overall_score: float
    robustness_level: RobustnessLevel
    passed_criteria: int
    total_criteria: int
    criteria_results: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    is_robust: bool


class RobustnessValidator:
    """Validador de critérios de robustez"""
    
    def __init__(self, criteria: Optional[RobustnessCriteria] = None):
        self.criteria = criteria or RobustnessCriteria()
    
    def validate_backtest_results(
        self,
        backtest_results: Dict[str, Any],
        walk_forward_results: Optional[Dict[str, Any]] = None,
        stress_test_results: Optional[Dict[str, Any]] = None
    ) -> RobustnessResult:
        """
        Valida resultados de backtest contra critérios de robustez
        
        Args:
            backtest_results: Resultados do backtest principal
            walk_forward_results: Resultados do walk-forward analysis
            stress_test_results: Resultados dos stress tests
        """
        logger.info("🔍 Iniciando validação de robustez")
        
        criteria_results = {}
        recommendations = []
        
        # 1. Validação de métricas básicas
        basic_metrics = self._validate_basic_metrics(backtest_results)
        criteria_results.update(basic_metrics)
        
        # 2. Validação de consistência (Walk-Forward)
        if walk_forward_results:
            consistency_metrics = self._validate_consistency(walk_forward_results)
            criteria_results.update(consistency_metrics)
        else:
            criteria_results['consistency'] = {
                'passed': False,
                'score': 0.0,
                'message': 'Walk-Forward Analysis não executado'
            }
            recommendations.append("Execute Walk-Forward Analysis para validar consistência")
        
        # 3. Validação de stress testing
        if stress_test_results:
            stress_metrics = self._validate_stress_tests(stress_test_results)
            criteria_results.update(stress_metrics)
        else:
            criteria_results['stress_testing'] = {
                'passed': False,
                'score': 0.0,
                'message': 'Stress Testing não executado'
            }
            recommendations.append("Execute Stress Testing para validar robustez")
        
        # 4. Validação de estabilidade temporal
        stability_metrics = self._validate_temporal_stability(backtest_results)
        criteria_results.update(stability_metrics)
        
        # 5. Calcular score geral
        overall_score, robustness_level = self._calculate_overall_score(criteria_results)
        
        # 6. Contar critérios passados
        passed_criteria = sum(1 for result in criteria_results.values() if result['passed'])
        total_criteria = len(criteria_results)
        
        # 7. Determinar se é robusto
        is_robust = (
            overall_score >= 0.7 and
            passed_criteria >= total_criteria * 0.8 and
            robustness_level in [RobustnessLevel.STRONG, RobustnessLevel.EXCELLENT]
        )
        
        # 8. Gerar recomendações
        if not is_robust:
            recommendations.extend(self._generate_recommendations(criteria_results))
        
        logger.info(f"✅ Validação concluída: Score={overall_score:.2f}, Nível={robustness_level.value}")
        
        return RobustnessResult(
            overall_score=overall_score,
            robustness_level=robustness_level,
            passed_criteria=passed_criteria,
            total_criteria=total_criteria,
            criteria_results=criteria_results,
            recommendations=recommendations,
            is_robust=is_robust
        )
    
    def _validate_basic_metrics(self, backtest_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Valida métricas básicas de performance"""
        results = {}
        
        # Sharpe Ratio
        sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
        results['sharpe_ratio'] = {
            'passed': sharpe_ratio >= self.criteria.min_sharpe_ratio,
            'score': min(1.0, sharpe_ratio / self.criteria.min_sharpe_ratio),
            'value': sharpe_ratio,
            'threshold': self.criteria.min_sharpe_ratio,
            'message': f"Sharpe Ratio: {sharpe_ratio:.2f} (mínimo: {self.criteria.min_sharpe_ratio})"
        }
        
        # Maximum Drawdown
        max_drawdown = backtest_results.get('max_drawdown', 1.0)
        results['max_drawdown'] = {
            'passed': max_drawdown <= self.criteria.max_drawdown,
            'score': max(0.0, 1.0 - max_drawdown / self.criteria.max_drawdown),
            'value': max_drawdown,
            'threshold': self.criteria.max_drawdown,
            'message': f"Max Drawdown: {max_drawdown:.1%} (máximo: {self.criteria.max_drawdown:.1%})"
        }
        
        # Profit Factor
        profit_factor = backtest_results.get('profit_factor', 0.0)
        results['profit_factor'] = {
            'passed': profit_factor >= self.criteria.min_profit_factor,
            'score': min(1.0, profit_factor / self.criteria.min_profit_factor),
            'value': profit_factor,
            'threshold': self.criteria.min_profit_factor,
            'message': f"Profit Factor: {profit_factor:.2f} (mínimo: {self.criteria.min_profit_factor})"
        }
        
        # Win Rate
        win_rate = backtest_results.get('win_rate', 0.0)
        results['win_rate'] = {
            'passed': win_rate >= self.criteria.min_win_rate,
            'score': min(1.0, win_rate / self.criteria.min_win_rate),
            'value': win_rate,
            'threshold': self.criteria.min_win_rate,
            'message': f"Win Rate: {win_rate:.1%} (mínimo: {self.criteria.min_win_rate:.1%})"
        }
        
        # Número de Trades
        total_trades = backtest_results.get('total_trades', 0)
        results['total_trades'] = {
            'passed': total_trades >= self.criteria.min_trades,
            'score': min(1.0, total_trades / self.criteria.min_trades),
            'value': total_trades,
            'threshold': self.criteria.min_trades,
            'message': f"Total Trades: {total_trades} (mínimo: {self.criteria.min_trades})"
        }
        
        return results
    
    def _validate_consistency(self, walk_forward_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Valida consistência via Walk-Forward Analysis"""
        results = {}
        
        consolidated_metrics = walk_forward_results.get('consolidated_metrics', {})
        
        # Consistência de Win Rate
        win_rate_std = consolidated_metrics.get('win_rate_std', 1.0)
        consistency_score = consolidated_metrics.get('consistency_score', 0.0)
        
        results['consistency'] = {
            'passed': consistency_score >= self.criteria.min_consistency_score,
            'score': consistency_score,
            'value': consistency_score,
            'threshold': self.criteria.min_consistency_score,
            'message': f"Consistência: {consistency_score:.1%} (mínimo: {self.criteria.min_consistency_score:.1%})"
        }
        
        # Estabilidade do Sharpe
        sharpe_std = consolidated_metrics.get('sharpe_std', 1.0)
        avg_sharpe = consolidated_metrics.get('avg_sharpe_ratio', 0.0)
        sharpe_stability = max(0.0, 1.0 - sharpe_std / max(0.1, avg_sharpe))
        
        results['sharpe_stability'] = {
            'passed': sharpe_stability >= 0.5,
            'score': sharpe_stability,
            'value': sharpe_stability,
            'threshold': 0.5,
            'message': f"Estabilidade Sharpe: {sharpe_stability:.1%} (mínimo: 50%)"
        }
        
        return results
    
    def _validate_stress_tests(self, stress_test_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Valida resultados dos stress tests"""
        results = {}
        
        # Analisar cada cenário de stress
        scenario_scores = []
        
        for scenario_name, scenario_result in stress_test_results.items():
            if isinstance(scenario_result, dict) and 'success_rate' in scenario_result:
                success_rate = scenario_result['success_rate']
                scenario_scores.append(success_rate)
        
        if scenario_scores:
            avg_success_rate = np.mean(scenario_scores)
            min_success_rate = np.min(scenario_scores)
            
            results['stress_testing'] = {
                'passed': min_success_rate >= 0.3,  # Pelo menos 30% em todos os cenários
                'score': avg_success_rate,
                'value': avg_success_rate,
                'threshold': 0.3,
                'message': f"Stress Testing: {avg_success_rate:.1%} sucesso médio (mínimo: 30%)"
            }
            
            # Cenário mais crítico
            worst_scenario = min(stress_test_results.items(), 
                               key=lambda x: x[1].get('success_rate', 0) if isinstance(x[1], dict) else 0)
            
            results['worst_case'] = {
                'passed': worst_scenario[1].get('success_rate', 0) >= 0.2,
                'score': worst_scenario[1].get('success_rate', 0),
                'value': worst_scenario[1].get('success_rate', 0),
                'threshold': 0.2,
                'message': f"Pior cenário ({worst_scenario[0]}): {worst_scenario[1].get('success_rate', 0):.1%}"
            }
        else:
            results['stress_testing'] = {
                'passed': False,
                'score': 0.0,
                'value': 0.0,
                'threshold': 0.3,
                'message': 'Nenhum resultado de stress test válido'
            }
        
        return results
    
    def _validate_temporal_stability(self, backtest_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Valida estabilidade temporal"""
        results = {}
        
        # Análise de volatilidade dos retornos
        returns = backtest_results.get('returns', pd.Series())
        if not returns.empty:
            volatility = returns.std() * np.sqrt(252)  # Anualizada
            
            results['volatility'] = {
                'passed': volatility <= self.criteria.max_volatility,
                'score': max(0.0, 1.0 - volatility / self.criteria.max_volatility),
                'value': volatility,
                'threshold': self.criteria.max_volatility,
                'message': f"Volatilidade: {volatility:.1%} (máximo: {self.criteria.max_volatility:.1%})"
            }
            
            # Calmar Ratio (Return / Max Drawdown)
            total_return = backtest_results.get('total_return', 0.0)
            max_drawdown = backtest_results.get('max_drawdown', 1.0)
            calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
            
            results['calmar_ratio'] = {
                'passed': calmar_ratio >= self.criteria.min_calmar_ratio,
                'score': min(1.0, calmar_ratio / self.criteria.min_calmar_ratio),
                'value': calmar_ratio,
                'threshold': self.criteria.min_calmar_ratio,
                'message': f"Calmar Ratio: {calmar_ratio:.2f} (mínimo: {self.criteria.min_calmar_ratio})"
            }
        else:
            results['volatility'] = {
                'passed': False,
                'score': 0.0,
                'value': 0.0,
                'threshold': self.criteria.max_volatility,
                'message': 'Dados de retorno não disponíveis'
            }
        
        return results
    
    def _calculate_overall_score(self, criteria_results: Dict[str, Dict[str, Any]]) -> Tuple[float, RobustnessLevel]:
        """Calcula score geral e nível de robustez"""
        
        if not criteria_results:
            return 0.0, RobustnessLevel.FAILED
        
        # Calcular score médio
        scores = [result['score'] for result in criteria_results.values()]
        overall_score = np.mean(scores)
        
        # Determinar nível de robustez
        if overall_score >= 0.9:
            level = RobustnessLevel.EXCELLENT
        elif overall_score >= 0.8:
            level = RobustnessLevel.STRONG
        elif overall_score >= 0.6:
            level = RobustnessLevel.MODERATE
        elif overall_score >= 0.4:
            level = RobustnessLevel.WEAK
        else:
            level = RobustnessLevel.FAILED
        
        return overall_score, level
    
    def _generate_recommendations(self, criteria_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """Gera recomendações para melhorar robustez"""
        recommendations = []
        
        for criterion, result in criteria_results.items():
            if not result['passed']:
                if criterion == 'sharpe_ratio':
                    recommendations.append("Melhore o Sharpe Ratio otimizando a relação retorno/risco")
                elif criterion == 'max_drawdown':
                    recommendations.append("Implemente controles de risco mais rigorosos para reduzir drawdown")
                elif criterion == 'profit_factor':
                    recommendations.append("Melhore a qualidade dos sinais para aumentar profit factor")
                elif criterion == 'win_rate':
                    recommendations.append("Refine critérios de entrada para aumentar win rate")
                elif criterion == 'total_trades':
                    recommendations.append("Execute backtest com período mais longo para obter mais trades")
                elif criterion == 'consistency':
                    recommendations.append("Execute Walk-Forward Analysis para validar consistência")
                elif criterion == 'stress_testing':
                    recommendations.append("Execute Stress Testing para validar robustez em cenários adversos")
                elif criterion == 'volatility':
                    recommendations.append("Implemente controles de volatilidade")
                elif criterion == 'calmar_ratio':
                    recommendations.append("Melhore retorno ajustado ao risco")
        
        return recommendations
    
    def generate_report(self, robustness_result: RobustnessResult) -> str:
        """Gera relatório de robustez"""
        
        report = f"""
# Relatório de Validação de Robustez

## Resumo Geral
- **Score Geral**: {robustness_result.overall_score:.2f}
- **Nível de Robustez**: {robustness_result.robustness_level.value}
- **Critérios Passados**: {robustness_result.passed_criteria}/{robustness_result.total_criteria}
- **É Robusto**: {'✅ SIM' if robustness_result.is_robust else '❌ NÃO'}

## Detalhes por Critério
"""
        
        for criterion, result in robustness_result.criteria_results.items():
            status = "✅" if result['passed'] else "❌"
            report += f"\n### {criterion.replace('_', ' ').title()}\n"
            report += f"- **Status**: {status} {'PASSOU' if result['passed'] else 'FALHOU'}\n"
            report += f"- **Score**: {result['score']:.2f}\n"
            report += f"- **Valor**: {result['value']:.4f}\n"
            report += f"- **Threshold**: {result['threshold']:.4f}\n"
            report += f"- **Mensagem**: {result['message']}\n"
        
        if robustness_result.recommendations:
            report += "\n## Recomendações\n"
            for i, rec in enumerate(robustness_result.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        return report
