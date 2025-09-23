#!/usr/bin/env python3
"""
Teste Simples do Sistema de Geração de Sinais CLI
Usa dados simulados para testar o pipeline completo
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.signal_generation import CLICalculator, SignalGenerator, MLOptimizer, PositionSizing

def create_simulated_data():
    """Cria dados simulados para teste"""
    
    # Criar datas dos últimos 60 meses
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1825)  # 60 meses
    dates = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    # Dados econômicos simulados
    economic_data = {}
    
    # IPCA (inflação) - tendência crescente
    ipca_trend = np.linspace(3.0, 5.5, len(dates))
    ipca_noise = np.random.normal(0, 0.5, len(dates))
    economic_data['ipca'] = pd.DataFrame({
        'date': dates,
        'value': ipca_trend + ipca_noise
    })
    
    # SELIC (taxa de juros) - tendência decrescente
    selic_trend = np.linspace(13.75, 10.5, len(dates))
    selic_noise = np.random.normal(0, 0.2, len(dates))
    economic_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': selic_trend + selic_noise
    })
    
    # Câmbio (USD/BRL) - volatilidade alta
    cambio_base = 5.0
    cambio_trend = np.cumsum(np.random.normal(0, 0.1, len(dates)))
    economic_data['cambio'] = pd.DataFrame({
        'date': dates,
        'value': cambio_base + cambio_trend
    })
    
    # Produção Industrial - cíclica
    prod_cycle = 100 + 10 * np.sin(np.linspace(0, 4*np.pi, len(dates)))
    prod_noise = np.random.normal(0, 2, len(dates))
    economic_data['prod_industrial'] = pd.DataFrame({
        'date': dates,
        'value': prod_cycle + prod_noise
    })
    
    # PIB - crescimento moderado
    pib_trend = 100 + np.cumsum(np.random.normal(0.3, 0.5, len(dates)))
    economic_data['pib'] = pd.DataFrame({
        'date': dates,
        'value': pib_trend
    })
    
    # Desemprego - tendência decrescente
    desemprego_trend = np.linspace(12.0, 8.5, len(dates))
    desemprego_noise = np.random.normal(0, 0.5, len(dates))
    economic_data['desemprego'] = pd.DataFrame({
        'date': dates,
        'value': desemprego_trend + desemprego_noise
    })
    
    return economic_data

def test_signal_generation_pipeline():
    """Testa o pipeline completo de geração de sinais com dados simulados"""
    
    print("🚀 Iniciando teste do sistema de geração de sinais (dados simulados)...")
    
    try:
        # 1. Criar dados simulados
        print("\n📊 1. Criando dados econômicos simulados...")
        economic_data = create_simulated_data()
        
        print(f"✅ Dados criados: {len(economic_data)} séries")
        for series_name, df in economic_data.items():
            print(f"   - {series_name}: {len(df)} pontos")
        
        # 2. Calcular CLI
        print("\n🧮 2. Calculando CLI...")
        cli_calculator = CLICalculator()
        cli_data = cli_calculator.calculate_cli(economic_data)
        
        if cli_data.empty:
            print("❌ Falha no cálculo do CLI")
            return False
        
        print(f"✅ CLI calculado: {len(cli_data)} pontos")
        print(f"   - CLI atual: {cli_data['cli_normalized'].iloc[-1]:.2f}")
        print(f"   - Tendência: {cli_data['cli_trend'].iloc[-1]:.2f}")
        print(f"   - Momentum: {cli_data['cli_momentum'].iloc[-1]:.2f}")
        
        # 3. Gerar sinais
        print("\n📈 3. Gerando sinais de trading...")
        signal_generator = SignalGenerator()
        signals_data = signal_generator.generate_signals(cli_data, economic_data)
        
        if signals_data.empty:
            print("❌ Falha na geração de sinais")
            return False
        
        print(f"✅ Sinais gerados: {len(signals_data)} pontos")
        
        # Resumo dos sinais
        signal_summary = signal_generator.get_signal_summary(signals_data)
        print(f"   - Total de sinais: {signal_summary['total_signals']}")
        print(f"   - BUY: {signal_summary['buy_signals']} ({signal_summary['buy_percentage']:.1f}%)")
        print(f"   - SELL: {signal_summary['sell_signals']} ({signal_summary['sell_percentage']:.1f}%)")
        print(f"   - HOLD: {signal_summary['hold_signals']} ({signal_summary['hold_percentage']:.1f}%)")
        print(f"   - Confiança média: {signal_summary['average_confidence']:.3f}")
        print(f"   - Força média: {signal_summary['average_strength']:.2f}")
        print(f"   - Último sinal: {signal_summary['last_signal']}")
        
        # 4. Otimizar com ML
        print("\n🤖 4. Otimizando com Machine Learning...")
        ml_optimizer = MLOptimizer()
        
        # Criar dados de retorno simulados para teste
        returns_data = pd.Series(
            np.random.normal(0.001, 0.02, len(cli_data)),
            index=cli_data.index
        )
        
        # Otimizar pesos
        optimized_weights = ml_optimizer.optimize_signal_weights(
            economic_data['ipca'],  # Usar IPCA como features
            returns_data,
            signals_data
        )
        
        print(f"✅ Pesos otimizados: {optimized_weights}")
        
        # Resumo da otimização
        optimization_summary = ml_optimizer.get_optimization_summary()
        if optimization_summary['status'] == 'optimized':
            print(f"   - R² do ensemble: {optimization_summary['performance']['r2']:.3f}")
            print(f"   - RMSE: {optimization_summary['performance']['rmse']:.4f}")
        
        # 5. Calcular tamanhos de posição
        print("\n💰 5. Calculando tamanhos de posição...")
        position_sizing = PositionSizing()
        positions_data = position_sizing.calculate_position_size(
            signals_data,
            returns_data,
            current_capital=100000.0
        )
        
        if positions_data.empty:
            print("❌ Falha no cálculo de posições")
            return False
        
        print(f"✅ Posições calculadas: {len(positions_data)} pontos")
        
        # Resumo das posições
        position_summary = position_sizing.get_position_summary(positions_data)
        if 'error' not in position_summary:
            print(f"   - Posições ativas: {position_summary['total_positions']}")
            print(f"   - Exposição total: R$ {position_summary['total_exposure']:,.2f}")
            print(f"   - Exposição %: {position_summary['exposure_percentage']:.2f}%")
            print(f"   - Tamanho médio: {position_summary['average_position_size']:.4f}")
            print(f"   - Volatilidade portfolio: {position_summary['portfolio_volatility']:.4f}")
            print(f"   - Sharpe portfolio: {position_summary['portfolio_sharpe']:.4f}")
        
        # 6. Verificar status de saúde
        print("\n🏥 6. Verificando status de saúde...")
        health_status = {
            'cli_calculator': cli_calculator.get_cli_health_status(),
            'signal_generator': signal_generator.get_signal_health_status(),
            'ml_optimizer': ml_optimizer.get_ml_health_status(),
            'position_sizing': position_sizing.get_position_health_status()
        }
        
        for component, status in health_status.items():
            print(f"   - {component}: {status['status']}")
        
        # 7. Mostrar últimos sinais
        print("\n📋 7. Últimos sinais gerados:")
        last_signals = signals_data.tail(5)
        for idx, row in last_signals.iterrows():
            date_str = str(idx) if hasattr(idx, 'strftime') else f"Ponto {idx}"
            print(f"   {date_str}: {row['signal_type']} "
                  f"(força: {row['signal_strength']}, confiança: {row['signal_confidence']:.3f}, "
                  f"CLI: {row['cli_normalized']:.2f})")
        
        print("\n✅ Teste do sistema de geração de sinais concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Testa componentes individuais"""
    print("\n🔧 Testando componentes individuais...")
    
    # Teste CLI Calculator
    print("\n1. Testando CLI Calculator...")
    cli_calc = CLICalculator()
    health = cli_calc.get_cli_health_status()
    print(f"   Status: {health['status']}")
    
    # Teste Signal Generator
    print("\n2. Testando Signal Generator...")
    signal_gen = SignalGenerator()
    health = signal_gen.get_signal_health_status()
    print(f"   Status: {health['status']}")
    
    # Teste ML Optimizer
    print("\n3. Testando ML Optimizer...")
    ml_opt = MLOptimizer()
    health = ml_opt.get_ml_health_status()
    print(f"   Status: {health['status']}")
    
    # Teste Position Sizing
    print("\n4. Testando Position Sizing...")
    pos_sizing = PositionSizing()
    health = pos_sizing.get_position_health_status()
    print(f"   Status: {health['status']}")

if __name__ == "__main__":
    print("🧪 TESTE SIMPLES DO SISTEMA DE GERAÇÃO DE SINAIS CLI")
    print("=" * 60)
    
    # Testar componentes individuais primeiro
    test_individual_components()
    
    # Executar teste completo
    success = test_signal_generation_pipeline()
    
    if success:
        print("\n🎉 Todos os testes passaram!")
        exit(0)
    else:
        print("\n💥 Alguns testes falharam!")
        exit(1)
