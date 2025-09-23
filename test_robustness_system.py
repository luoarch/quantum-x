"""
Teste do Sistema de Robustez em 4 Camadas
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.robust_data_collector import RobustDataCollector
from app.services.backtesting.walk_forward_analysis import WalkForwardAnalysis
from app.services.backtesting.stress_testing import MonteCarloStressTester
from app.services.ml.ensemble_model import EnsembleModel
from app.services.validation.robustness_validator import RobustnessValidator, RobustnessCriteria
from app.core.database import SessionLocal, init_db


class MockSignalGenerator:
    """Gerador de sinais mockado para teste"""
    
    def __init__(self):
        self.threshold = 100.5
        self.trained = False
    
    def fit(self, data: pd.DataFrame):
        """Simula treinamento"""
        self.trained = True
        print("✅ Modelo treinado (mock)")
    
    def generate_signal(self, row: pd.Series) -> str:
        """Gera sinal baseado em threshold simples"""
        if not self.trained:
            return "HOLD"
        
        value = row.get('value', 100)
        
        if value > self.threshold:
            return "BUY"
        elif value < (self.threshold - 0.5):
            return "SELL"
        else:
            return "HOLD"


async def test_robustness_system():
    """Testa o sistema completo de robustez"""
    print("🚀 Iniciando teste do Sistema de Robustez em 4 Camadas")
    
    # 1. Inicializar banco de dados
    await init_db()
    print("✅ Banco de dados inicializado")
    
    # 2. Camada 1: Teste de Integridade dos Dados
    print("\n" + "="*50)
    print("CAMADA 1: INTEGRIDADE DOS DADOS")
    print("="*50)
    
    db = SessionLocal()
    try:
        collector = RobustDataCollector()
        
        # Testar coleta robusta
        print("🔄 Testando coleta robusta de dados...")
        result = await collector.collect_all_data(db)
        
        print(f"✅ Coleta concluída:")
        print(f"   - Dados econômicos: {result['economic_data']['total_records']} registros")
        print(f"   - Dados CLI: {result['cli_data']['total_records']} registros")
        print(f"   - Total: {result['total_records']} registros")
        
        # Verificar saúde das fontes
        health = collector.get_sources_health()
        print(f"📊 Saúde das fontes:")
        for source_type, sources in health.items():
            for source in sources:
                status = "✅" if source['is_available'] else "❌"
                print(f"   - {source['name']}: {status} (score: {source['health_score']:.2f})")
        
    except Exception as e:
        print(f"❌ Erro na coleta de dados: {e}")
        return
    
    finally:
        db.close()
    
    # 3. Camada 2: Teste de Backtesting Científico
    print("\n" + "="*50)
    print("CAMADA 2: BACKTESTING CIENTÍFICO")
    print("="*50)
    
    # Criar dados mockados para teste
    print("🔄 Gerando dados mockados para backtesting...")
    mock_data = generate_mock_data()
    
    # Walk-Forward Analysis
    print("🔄 Executando Walk-Forward Analysis...")
    wf_analyzer = WalkForwardAnalysis(
        train_period_years=2,
        test_period_months=6,
        min_trades=5
    )
    
    signal_generator = MockSignalGenerator()
    
    try:
        wf_results = wf_analyzer.run_analysis(mock_data, signal_generator)
        print(f"✅ Walk-Forward concluído:")
        print(f"   - Janelas válidas: {wf_results['valid_windows']}/{wf_results['total_windows']}")
        print(f"   - Score de consistência: {wf_results['consolidated_metrics']['consistency_score']:.2f}")
    except Exception as e:
        print(f"❌ Erro no Walk-Forward: {e}")
        wf_results = None
    
    # 4. Camada 3: Teste de Stress Testing
    print("\n" + "="*50)
    print("CAMADA 3: STRESS TESTING")
    print("="*50)
    
    print("🔄 Executando Stress Testing com Monte Carlo...")
    stress_tester = MonteCarloStressTester(
        n_simulations=1000,  # Reduzido para teste rápido
        robust_criteria={
            'min_sharpe': 0.5,  # Relaxado para teste
            'max_drawdown': 0.30,
            'min_profit_factor': 1.2,
            'min_win_rate': 0.45
        }
    )
    
    try:
        stress_results = stress_tester.run_stress_tests(mock_data, signal_generator)
        print(f"✅ Stress Testing concluído:")
        for scenario, result in stress_results.items():
            print(f"   - {scenario}: {result.success_rate:.1%} simulações robustas")
    except Exception as e:
        print(f"❌ Erro no Stress Testing: {e}")
        stress_results = None
    
    # 5. Camada 4: Teste de Validação do Modelo de IA
    print("\n" + "="*50)
    print("CAMADA 4: VALIDAÇÃO DO MODELO DE IA")
    print("="*50)
    
    print("🔄 Testando Ensemble de Modelos...")
    
    # Preparar dados para ML
    X, y = prepare_ml_data(mock_data)
    
    try:
        ensemble = EnsembleModel()
        training_results = ensemble.fit(X, y)
        
        print(f"✅ Ensemble treinado:")
        for model_name, result in training_results['training_results'].items():
            if result['status'] == 'success':
                print(f"   - {model_name}: Score={result['validation_score']:.4f}")
        
        # Testar predição
        predictions, individual_preds = ensemble.predict(X.head(10))
        print(f"   - Predições geradas: {len(predictions)} amostras")
        
        # Testar explicação
        explanations = ensemble.explain_prediction(X.head(5))
        print(f"   - Explicações SHAP: {len(explanations)} modelos")
        
    except Exception as e:
        print(f"❌ Erro no Ensemble: {e}")
        ensemble = None
    
    # 6. Validação Final de Robustez
    print("\n" + "="*50)
    print("VALIDAÇÃO FINAL DE ROBUSTEZ")
    print("="*50)
    
    print("🔄 Executando validação de critérios de robustez...")
    
    # Preparar resultados para validação
    backtest_results = {
        'sharpe_ratio': 1.2,
        'max_drawdown': 0.15,
        'profit_factor': 1.8,
        'win_rate': 0.65,
        'total_trades': 150,
        'total_return': 0.25,
        'returns': pd.Series(np.random.normal(0.001, 0.02, 1000))
    }
    
    validator = RobustnessValidator()
    
    try:
        robustness_result = validator.validate_backtest_results(
            backtest_results=backtest_results,
            walk_forward_results=wf_results,
            stress_test_results=stress_results
        )
        
        print(f"✅ Validação concluída:")
        print(f"   - Score Geral: {robustness_result.overall_score:.2f}")
        print(f"   - Nível: {robustness_result.robustness_level.value}")
        print(f"   - Critérios Passados: {robustness_result.passed_criteria}/{robustness_result.total_criteria}")
        print(f"   - É Robusto: {'✅ SIM' if robustness_result.is_robust else '❌ NÃO'}")
        
        if robustness_result.recommendations:
            print(f"\n📋 Recomendações:")
            for i, rec in enumerate(robustness_result.recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Gerar relatório
        report = validator.generate_report(robustness_result)
        print(f"\n📄 Relatório gerado ({len(report)} caracteres)")
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
    
    print("\n" + "="*50)
    print("✅ TESTE DO SISTEMA DE ROBUSTEZ CONCLUÍDO")
    print("="*50)


def generate_mock_data() -> pd.DataFrame:
    """Gera dados mockados para teste"""
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
    
    # Simular dados econômicos com tendência e sazonalidade
    np.random.seed(42)
    n = len(dates)
    
    # Tendência
    trend = np.linspace(100, 110, n)
    
    # Sazonalidade
    seasonal = 2 * np.sin(2 * np.pi * np.arange(n) / 12)
    
    # Ruído
    noise = np.random.normal(0, 1, n)
    
    # Valores finais
    values = trend + seasonal + noise
    
    return pd.DataFrame({
        'date': dates,
        'value': values,
        'series_name': 'MOCK_ECONOMIC',
        'source': 'MOCK'
    })


def prepare_ml_data(data: pd.DataFrame) -> tuple:
    """Prepara dados para machine learning"""
    # Features simples: valor, média móvel, desvio padrão
    data = data.copy()
    data['ma_3'] = data['value'].rolling(3).mean()
    data['ma_12'] = data['value'].rolling(12).mean()
    data['std_3'] = data['value'].rolling(3).std()
    data['std_12'] = data['value'].rolling(12).std()
    
    # Target: retorno futuro (simplificado)
    data['future_return'] = data['value'].shift(-1) / data['value'] - 1
    
    # Remover NaN
    data = data.dropna()
    
    # Features
    feature_cols = ['value', 'ma_3', 'ma_12', 'std_3', 'std_12']
    X = data[feature_cols]
    y = data['future_return']
    
    return X, y


if __name__ == "__main__":
    asyncio.run(test_robustness_system())
