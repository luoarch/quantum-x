#!/usr/bin/env python3
"""
Teste de Backtesting Histórico
Executa backtesting rigoroso com dados históricos reais para validar a estratégia CLI
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.backtesting import HistoricalBacktester, PerformanceAnalyzer, AssetSimulator

async def test_historical_backtest():
    """Executa backtesting histórico completo"""
    
    print("🚀 INICIANDO BACKTESTING HISTÓRICO - ESTRATÉGIA CLI")
    print("=" * 60)
    
    try:
        # 1. Configurar período de backtesting
        print("\n📅 1. Configurando período de backtesting...")
        start_date = "2020-01-01"  # Começar com 5 anos para teste
        end_date = "2025-09-23"
        
        print(f"   Período: {start_date} a {end_date}")
        print(f"   Duração: ~5.7 anos")
        
        # 2. Inicializar backtester
        print("\n🔧 2. Inicializando backtester...")
        backtester = HistoricalBacktester(
            initial_capital=100000.0,
            transaction_cost=0.001,  # 0.1% por transação
            risk_free_rate=0.05      # 5% ao ano
        )
        
        # 3. Executar backtesting
        print("\n⚡ 3. Executando backtesting histórico...")
        print("   (Isso pode levar alguns minutos...)")
        
        result = await backtester.run_historical_backtest(
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly"
        )
        
        # 4. Exibir resultados
        print("\n📊 4. RESULTADOS DO BACKTESTING")
        print("=" * 40)
        
        print(f"💰 Retorno Total: {result.total_return:.2%}")
        print(f"📈 Retorno Anualizado: {result.annualized_return:.2%}")
        print(f"📉 Maximum Drawdown: {result.max_drawdown:.2%}")
        print(f"⚡ Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"🎯 Taxa de Vitória: {result.win_rate:.2%}")
        print(f"📊 Total de Trades: {result.total_trades}")
        print(f"💵 Capital Final: R$ {result.final_capital:,.2f}")
        
        # 5. Análise de performance detalhada
        print("\n🔍 5. ANÁLISE DETALHADA DE PERFORMANCE")
        print("=" * 45)
        
        analyzer = PerformanceAnalyzer()
        
        # Usar dados do backtester para análise
        if hasattr(backtester, 'portfolio_values') and backtester.portfolio_values:
            detailed_metrics = analyzer.analyze_performance(
                backtester.portfolio_values,
                backtester.trades
            )
            
            print(f"📊 Volatilidade Anual: {detailed_metrics.volatility:.2%}")
            print(f"⏱️ Duração Máx. Drawdown: {detailed_metrics.max_drawdown_duration} dias")
            print(f"🎲 Profit Factor: {detailed_metrics.profit_factor:.2f}")
            print(f"💎 Expectativa: {detailed_metrics.expectancy:.2%}")
            print(f"📈 Sortino Ratio: {detailed_metrics.sortino_ratio:.2f}")
            print(f"📉 Calmar Ratio: {detailed_metrics.calmar_ratio:.2f}")
        
        # 6. Avaliação da estratégia
        print("\n🎯 6. AVALIAÇÃO DA ESTRATÉGIA")
        print("=" * 35)
        
        # Critérios de avaliação
        sharpe_ok = result.sharpe_ratio > 0.5
        drawdown_ok = result.max_drawdown > -0.20
        win_rate_ok = result.win_rate > 0.50
        return_ok = result.annualized_return > 0.05
        
        print(f"Sharpe Ratio > 0.5: {'✅' if sharpe_ok else '❌'} ({result.sharpe_ratio:.2f})")
        print(f"Drawdown < 20%: {'✅' if drawdown_ok else '❌'} ({result.max_drawdown:.2%})")
        print(f"Taxa Vitória > 50%: {'✅' if win_rate_ok else '❌'} ({result.win_rate:.2%})")
        print(f"Retorno > 5% a.a.: {'✅' if return_ok else '❌'} ({result.annualized_return:.2%})")
        
        # Score geral
        score = sum([sharpe_ok, drawdown_ok, win_rate_ok, return_ok])
        print(f"\n🏆 Score Geral: {score}/4")
        
        if score >= 3:
            print("🎉 ESTRATÉGIA APROVADA - Pronta para produção!")
        elif score >= 2:
            print("⚠️ ESTRATÉGIA PARCIALMENTE APROVADA - Necessita ajustes")
        else:
            print("❌ ESTRATÉGIA REJEITADA - Necessita reformulação")
        
        # 7. Teste com ativos reais
        print("\n💼 7. TESTE COM ATIVOS REAIS")
        print("=" * 30)
        
        asset_simulator = AssetSimulator()
        
        # Carregar dados de ativos
        assets = await asset_simulator.load_asset_data(
            ['BOVA11', 'TESOURO_IPCA_2045'],
            start_date,
            end_date
        )
        
        if assets:
            print(f"✅ Ativos carregados: {list(assets.keys())}")
            
            # Testar com BOVA11
            if 'BOVA11' in assets:
                bova_result = asset_simulator.simulate_trading_with_assets(
                    backtester.signals_data,
                    'BOVA11',
                    100000.0
                )
                
                if bova_result:
                    print(f"📈 BOVA11 - Retorno: {bova_result['total_return']:.2%}")
                    print(f"📊 BOVA11 - Volatilidade: {bova_result['volatility']:.2%}")
                    print(f"💼 BOVA11 - Trades: {bova_result['total_trades']}")
            
            # Testar com Tesouro IPCA+
            if 'TESOURO_IPCA_2045' in assets:
                tesouro_result = asset_simulator.simulate_trading_with_assets(
                    backtester.signals_data,
                    'TESOURO_IPCA_2045',
                    100000.0
                )
                
                if tesouro_result:
                    print(f"🏛️ Tesouro IPCA+ - Retorno: {tesouro_result['total_return']:.2%}")
                    print(f"📊 Tesouro IPCA+ - Volatilidade: {tesouro_result['volatility']:.2%}")
                    print(f"💼 Tesouro IPCA+ - Trades: {tesouro_result['total_trades']}")
        
        # 8. Exportar resultados
        print("\n💾 8. EXPORTANDO RESULTADOS")
        print("=" * 30)
        
        try:
            filename = backtester.export_results()
            print(f"✅ Resultados exportados para: {filename}")
        except Exception as e:
            print(f"⚠️ Erro na exportação: {e}")
        
        # 9. Resumo final
        print("\n🎯 9. RESUMO FINAL")
        print("=" * 20)
        
        print(f"📅 Período: {result.start_date.strftime('%Y-%m-%d')} a {result.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Capital Inicial: R$ {result.initial_capital:,.2f}")
        print(f"💰 Capital Final: R$ {result.final_capital:,.2f}")
        print(f"📈 Retorno Total: {result.total_return:.2%}")
        print(f"⚡ Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"📉 Max Drawdown: {result.max_drawdown:.2%}")
        print(f"🎯 Taxa Vitória: {result.win_rate:.2%}")
        print(f"📊 Total Trades: {result.total_trades}")
        print(f"📈 Sinais Gerados: {result.signals_generated}")
        
        print("\n✅ BACKTESTING HISTÓRICO CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no backtesting histórico: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_quick_backtest():
    """Teste rápido com período menor"""
    print("🚀 TESTE RÁPIDO - BACKTESTING HISTÓRICO")
    print("=" * 50)
    
    try:
        # Período menor para teste rápido
        start_date = "2023-01-01"
        end_date = "2025-09-23"
        
        print(f"📅 Período: {start_date} a {end_date} (~2.7 anos)")
        
        backtester = HistoricalBacktester(
            initial_capital=50000.0,
            transaction_cost=0.001
        )
        
        result = await backtester.run_historical_backtest(
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n📊 RESULTADOS RÁPIDOS:")
        print(f"💰 Retorno: {result.total_return:.2%}")
        print(f"⚡ Sharpe: {result.sharpe_ratio:.2f}")
        print(f"📉 Drawdown: {result.max_drawdown:.2%}")
        print(f"🎯 Vitória: {result.win_rate:.2%}")
        print(f"📊 Trades: {result.total_trades}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste rápido: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE BACKTESTING HISTÓRICO")
    print("=" * 50)
    
    # Perguntar qual teste executar
    print("Escolha o tipo de teste:")
    print("1. Teste Completo (5+ anos) - Pode demorar")
    print("2. Teste Rápido (2.7 anos) - Mais rápido")
    
    choice = input("Digite 1 ou 2: ").strip()
    
    if choice == "1":
        success = asyncio.run(test_historical_backtest())
    elif choice == "2":
        success = asyncio.run(test_quick_backtest())
    else:
        print("❌ Opção inválida")
        success = False
    
    if success:
        print("\n🎉 Teste concluído com sucesso!")
        exit(0)
    else:
        print("\n💥 Teste falhou!")
        exit(1)
