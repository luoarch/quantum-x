#!/usr/bin/env python3
"""
Teste do Sistema de Geração de Sinais CLI
Testa o pipeline completo: CLI Calculator -> Signal Generator -> ML Optimizer -> Position Sizing
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
from app.services.signal_generation import CLICalculator, SignalGenerator, MLOptimizer, PositionSizing
from app.core.database import get_db
from app.models.time_series import EconomicSeries, CLISeries, TradingSignal
from sqlalchemy.orm import Session

async def test_signal_generation_pipeline():
    """Testa o pipeline completo de geração de sinais"""
    
    print("🚀 Iniciando teste do sistema de geração de sinais...")
    
    try:
        # 1. Coletar dados econômicos
        print("\n📊 1. Coletando dados econômicos...")
        db = next(get_db())
        collector = RobustDataCollector(db)
        
        # Coletar dados das últimas 24 meses
        collection_result = await collector.collect_all_series(months=24)
        economic_data = collection_result.get('economic', {})
        
        if not economic_data:
            print("❌ Falha na coleta de dados econômicos")
            return False
        
        print(f"✅ Dados coletados: {len(economic_data)} séries")
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
        
        # 6. Salvar no banco de dados
        print("\n💾 6. Salvando no banco de dados...")
        await save_signal_data_to_db(signals_data, positions_data, db)
        
        # 7. Verificar status de saúde
        print("\n🏥 7. Verificando status de saúde...")
        health_status = {
            'cli_calculator': cli_calculator.get_cli_health_status(),
            'signal_generator': signal_generator.get_signal_health_status(),
            'ml_optimizer': ml_optimizer.get_ml_health_status(),
            'position_sizing': position_sizing.get_position_health_status()
        }
        
        for component, status in health_status.items():
            print(f"   - {component}: {status['status']}")
        
        print("\n✅ Teste do sistema de geração de sinais concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def save_signal_data_to_db(signals_data: pd.DataFrame, positions_data: pd.DataFrame, db: Session):
    """Salva dados de sinais no banco de dados"""
    try:
        
        # Salvar sinais de trading
        for idx, row in signals_data.iterrows():
            signal = TradingSignal(
                date=idx,
                signal_type=row['signal_type'],
                signal_strength=int(row['signal_strength']),
                signal_confidence=float(row['signal_confidence']),
                cli_value=float(row['cli_normalized']),
                cli_momentum=float(row['cli_momentum']),
                cli_trend=float(row['cli_trend']),
                risk_level=int(row['risk_level']),
                position_size=float(positions_data.loc[idx, 'position_size']),
                position_value=float(positions_data.loc[idx, 'position_value']),
                stop_loss=float(positions_data.loc[idx, 'stop_loss']),
                take_profit=float(positions_data.loc[idx, 'take_profit'])
            )
            db.add(signal)
        
        db.commit()
        print(f"   - {len(signals_data)} sinais salvos no banco")
        
    except Exception as e:
        print(f"   - Erro ao salvar no banco: {e}")
    finally:
        db.close()

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
    print("🧪 TESTE DO SISTEMA DE GERAÇÃO DE SINAIS CLI")
    print("=" * 50)
    
    # Testar componentes individuais primeiro
    test_individual_components()
    
    # Executar teste completo
    success = asyncio.run(test_signal_generation_pipeline())
    
    if success:
        print("\n🎉 Todos os testes passaram!")
        exit(0)
    else:
        print("\n💥 Alguns testes falharam!")
        exit(1)
