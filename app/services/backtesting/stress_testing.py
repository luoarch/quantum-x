"""
Stress Testing com Monte Carlo Simulation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """Resultado de um teste de stress"""
    scenario_name: str
    total_simulations: int
    avg_return: float
    avg_sharpe: float
    avg_drawdown: float
    win_rate: float
    profit_factor: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional Value at Risk 95%
    success_rate: float  # % de simulações que passaram nos critérios
    results_distribution: Dict[str, List[float]]


class MonteCarloStressTester:
    """Testador de stress com simulação Monte Carlo"""
    
    def __init__(
        self,
        n_simulations: int = 10000,
        confidence_level: float = 0.95,
        robust_criteria: Optional[Dict[str, float]] = None
    ):
        self.n_simulations = n_simulations
        self.confidence_level = confidence_level
        self.robust_criteria = robust_criteria or {
            'min_sharpe': 1.0,
            'max_drawdown': 0.20,
            'min_profit_factor': 1.5,
            'min_win_rate': 0.55
        }
    
    def run_stress_tests(
        self,
        historical_data: pd.DataFrame,
        signal_generator,
        scenarios: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, StressTestResult]:
        """
        Executa testes de stress para múltiplos cenários
        
        Args:
            historical_data: Dados históricos para calibração
            signal_generator: Gerador de sinais
            scenarios: Cenários de stress personalizados
        """
        logger.info(f"🚀 Iniciando Stress Testing com {self.n_simulations} simulações")
        
        if scenarios is None:
            scenarios = self._get_default_scenarios()
        
        results = {}
        
        for scenario_name, scenario_config in scenarios.items():
            logger.info(f"🔄 Executando cenário: {scenario_name}")
            
            try:
                result = self._run_scenario_stress_test(
                    historical_data,
                    signal_generator,
                    scenario_name,
                    scenario_config
                )
                results[scenario_name] = result
                
                logger.info(f"✅ {scenario_name}: {result.success_rate:.1%} simulações robustas")
                
            except Exception as e:
                logger.error(f"❌ Erro no cenário {scenario_name}: {str(e)}")
                continue
        
        return results
    
    def _get_default_scenarios(self) -> Dict[str, Dict]:
        """Retorna cenários padrão de stress testing"""
        return {
            "baseline": {
                "description": "Cenário baseline com parâmetros históricos",
                "volatility_multiplier": 1.0,
                "drift_multiplier": 1.0,
                "correlation_shift": 0.0,
                "regime_change_prob": 0.0
            },
            "high_volatility": {
                "description": "Alta volatilidade (2x normal)",
                "volatility_multiplier": 2.0,
                "drift_multiplier": 1.0,
                "correlation_shift": 0.0,
                "regime_change_prob": 0.0
            },
            "low_volatility": {
                "description": "Baixa volatilidade (0.5x normal)",
                "volatility_multiplier": 0.5,
                "drift_multiplier": 1.0,
                "correlation_shift": 0.0,
                "regime_change_prob": 0.0
            },
            "bear_market": {
                "description": "Mercado em baixa (-2% drift anual)",
                "volatility_multiplier": 1.5,
                "drift_multiplier": -0.02,
                "correlation_shift": 0.2,
                "regime_change_prob": 0.1
            },
            "crisis_mode": {
                "description": "Modo crise (alta volatilidade + correlações altas)",
                "volatility_multiplier": 3.0,
                "drift_multiplier": -0.05,
                "correlation_shift": 0.5,
                "regime_change_prob": 0.3
            },
            "regime_shift": {
                "description": "Mudança de regime frequente",
                "volatility_multiplier": 1.2,
                "drift_multiplier": 1.0,
                "correlation_shift": 0.1,
                "regime_change_prob": 0.5
            }
        }
    
    def _run_scenario_stress_test(
        self,
        historical_data: pd.DataFrame,
        signal_generator,
        scenario_name: str,
        scenario_config: Dict
    ) -> StressTestResult:
        """Executa teste de stress para um cenário específico"""
        
        # Calibrar parâmetros do cenário
        calibrated_params = self._calibrate_scenario(historical_data, scenario_config)
        
        # Executar simulações Monte Carlo
        simulation_results = []
        
        for i in range(self.n_simulations):
            if i % 1000 == 0:
                logger.info(f"Simulação {i}/{self.n_simulations}")
            
            try:
                # Gerar caminho simulado
                simulated_data = self._generate_simulated_path(
                    historical_data,
                    calibrated_params,
                    scenario_config
                )
                
                # Executar estratégia no caminho simulado
                result = self._run_strategy_on_path(simulated_data, signal_generator)
                simulation_results.append(result)
                
            except Exception as e:
                logger.warning(f"Erro na simulação {i}: {e}")
                continue
        
        if not simulation_results:
            raise ValueError("Nenhuma simulação bem-sucedida")
        
        # Calcular métricas consolidadas
        return self._calculate_stress_metrics(scenario_name, simulation_results)
    
    def _calibrate_scenario(
        self,
        historical_data: pd.DataFrame,
        scenario_config: Dict
    ) -> Dict[str, Any]:
        """Calibra parâmetros do cenário baseado nos dados históricos"""
        
        # Calcular retornos históricos
        if 'value' in historical_data.columns:
            returns = historical_data['value'].pct_change().dropna()
        else:
            # Se não há coluna 'value', usar primeira coluna numérica
            numeric_cols = historical_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                returns = historical_data[numeric_cols[0]].pct_change().dropna()
            else:
                raise ValueError("Nenhuma coluna numérica encontrada para calcular retornos")
        
        # Parâmetros base
        base_volatility = returns.std() * np.sqrt(252)  # Anualizado
        base_drift = returns.mean() * 252  # Anualizado
        
        # Aplicar multiplicadores do cenário
        calibrated_volatility = base_volatility * scenario_config.get('volatility_multiplier', 1.0)
        calibrated_drift = base_drift * scenario_config.get('drift_multiplier', 1.0)
        
        return {
            'volatility': calibrated_volatility,
            'drift': calibrated_drift,
            'correlation_shift': scenario_config.get('correlation_shift', 0.0),
            'regime_change_prob': scenario_config.get('regime_change_prob', 0.0)
        }
    
    def _generate_simulated_path(
        self,
        historical_data: pd.DataFrame,
        calibrated_params: Dict,
        scenario_config: Dict
    ) -> pd.DataFrame:
        """Gera um caminho simulado usando Monte Carlo"""
        
        # Parâmetros da simulação
        n_periods = len(historical_data)
        dt = 1/252  # Um dia (assumindo dados diários)
        
        volatility = calibrated_params['volatility']
        drift = calibrated_params['drift']
        
        # Gerar choques aleatórios
        random_shocks = np.random.normal(0, 1, n_periods)
        
        # Aplicar mudança de regime se configurado
        if calibrated_params['regime_change_prob'] > 0:
            regime_changes = np.random.random(n_periods) < calibrated_params['regime_change_prob']
            # Durante mudanças de regime, aumentar volatilidade
            volatility_multiplier = np.where(regime_changes, 2.0, 1.0)
            random_shocks *= volatility_multiplier
        
        # Simular preços usando GBM (Geometric Brownian Motion)
        prices = [historical_data['value'].iloc[0]]  # Preço inicial
        
        for i in range(1, n_periods):
            # Fórmula GBM: S(t+1) = S(t) * exp((μ - σ²/2)dt + σ√dt * Z)
            price_change = np.exp(
                (drift - 0.5 * volatility**2) * dt + 
                volatility * np.sqrt(dt) * random_shocks[i]
            )
            new_price = prices[-1] * price_change
            prices.append(new_price)
        
        # Criar DataFrame simulado
        simulated_data = historical_data.copy()
        simulated_data['value'] = prices
        simulated_data['simulated'] = True
        
        return simulated_data
    
    def _run_strategy_on_path(
        self,
        simulated_data: pd.DataFrame,
        signal_generator
    ) -> Dict[str, float]:
        """Executa estratégia em um caminho simulado"""
        
        signals = []
        returns = []
        
        for _, row in simulated_data.iterrows():
            try:
                # Gerar sinal
                signal = signal_generator.generate_signal(row)
                signals.append(signal)
                
                # Calcular retorno (simplificado)
                if len(returns) > 0:
                    ret = (row['value'] - simulated_data.iloc[len(returns)-1]['value']) / simulated_data.iloc[len(returns)-1]['value']
                    returns.append(ret)
                else:
                    returns.append(0.0)
                    
            except Exception:
                signals.append('HOLD')
                returns.append(0.0)
        
        if not returns:
            return self._empty_result()
        
        returns_series = pd.Series(returns)
        
        # Calcular métricas
        total_return = returns_series.sum()
        sharpe_ratio = self._calculate_sharpe_ratio(returns_series)
        max_drawdown = self._calculate_max_drawdown(returns_series)
        win_rate = (returns_series > 0).mean()
        profit_factor = self._calculate_profit_factor(returns_series)
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'returns': returns_series.tolist()
        }
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calcula Sharpe Ratio"""
        if returns.std() == 0:
            return 0.0
        return returns.mean() / returns.std() * np.sqrt(252)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcula Maximum Drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
    
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        """Calcula Profit Factor"""
        positive_returns = returns[returns > 0].sum()
        negative_returns = abs(returns[returns < 0].sum())
        
        if negative_returns == 0:
            return float('inf') if positive_returns > 0 else 0.0
        
        return positive_returns / negative_returns
    
    def _calculate_stress_metrics(
        self,
        scenario_name: str,
        simulation_results: List[Dict[str, float]]
    ) -> StressTestResult:
        """Calcula métricas consolidadas do stress test"""
        
        # Extrair métricas de todas as simulações
        returns = [r['total_return'] for r in simulation_results]
        sharpes = [r['sharpe_ratio'] for r in simulation_results]
        drawdowns = [r['max_drawdown'] for r in simulation_results]
        win_rates = [r['win_rate'] for r in simulation_results]
        profit_factors = [r['profit_factor'] for r in simulation_results]
        
        # Calcular estatísticas
        avg_return = np.mean(returns)
        avg_sharpe = np.mean(sharpes)
        avg_drawdown = np.mean(drawdowns)
        win_rate = np.mean(win_rates)
        profit_factor = np.mean(profit_factors)
        
        # Value at Risk e Conditional VaR
        var_95 = np.percentile(returns, (1 - self.confidence_level) * 100)
        cvar_95 = np.mean([r for r in returns if r <= var_95])
        
        # Contar simulações que passaram nos critérios de robustez
        robust_simulations = sum(1 for r in simulation_results if self._is_robust_simulation(r))
        success_rate = robust_simulations / len(simulation_results)
        
        return StressTestResult(
            scenario_name=scenario_name,
            total_simulations=len(simulation_results),
            avg_return=avg_return,
            avg_sharpe=avg_sharpe,
            avg_drawdown=avg_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            var_95=var_95,
            cvar_95=cvar_95,
            success_rate=success_rate,
            results_distribution={
                'returns': returns,
                'sharpes': sharpes,
                'drawdowns': drawdowns,
                'win_rates': win_rates,
                'profit_factors': profit_factors
            }
        )
    
    def _is_robust_simulation(self, result: Dict[str, float]) -> bool:
        """Verifica se uma simulação atende aos critérios de robustez"""
        return (
            result['sharpe_ratio'] >= self.robust_criteria['min_sharpe'] and
            result['max_drawdown'] <= self.robust_criteria['max_drawdown'] and
            result['profit_factor'] >= self.robust_criteria['min_profit_factor'] and
            result['win_rate'] >= self.robust_criteria['min_win_rate']
        )
    
    def _empty_result(self) -> Dict[str, float]:
        """Retorna resultado vazio para simulações falhadas"""
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'returns': []
        }
