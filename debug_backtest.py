#!/usr/bin/env python3
"""
Debug do Backtesting - Vamos debugar passo a passo
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.signal_generation import CLICalculator, SignalGenerator

def create_simple_data():
    """Cria dados simples para debug"""
    print("🔧 Criando dados simples para debug...")
    
    # Criar apenas 12 meses de dados
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq='ME')
    
    economic_data = {}
    
    # IPCA simples
    economic_data['ipca'] = pd.DataFrame({
        'date': dates,
        'value': [4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6]
    })
    
    # SELIC simples
    economic_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': [10.5, 10.6, 10.7, 10.8, 10.9, 11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6]
    })
    
    # Câmbio simples
    economic_data['cambio'] = pd.DataFrame({
        'date': dates,
        'value': [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1]
    })
    
    # Produção Industrial simples
    economic_data['prod_industrial'] = pd.DataFrame({
        'date': dates,
        'value': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
    })
    
    # PIB simples
    economic_data['pib'] = pd.DataFrame({
        'date': dates,
        'value': [100, 100.5, 101, 101.5, 102, 102.5, 103, 103.5, 104, 104.5, 105, 105.5]
    })
    
    # Desemprego simples
    economic_data['desemprego'] = pd.DataFrame({
        'date': dates,
        'value': [8.0, 7.9, 7.8, 7.7, 7.6, 7.5, 7.4, 7.3, 7.2, 7.1, 7.0, 6.9]
    })
    
    print(f"✅ Dados criados: {len(economic_data)} séries")
    for series_name, df in economic_data.items():
        print(f"   - {series_name}: {len(df)} pontos")
        print(f"     Primeiro valor: {df['value'].iloc[0]}")
        print(f"     Último valor: {df['value'].iloc[-1]}")
    
    return economic_data

def debug_cli_calculation():
    """Debug do cálculo do CLI"""
    print("\n🧮 DEBUG: Cálculo do CLI")
    print("=" * 30)
    
    try:
        # Criar dados simples
        economic_data = create_simple_data()
        
        # Inicializar calculador CLI
        cli_calculator = CLICalculator()
        
        # Ajustar requisito mínimo para 12 pontos
        cli_calculator.min_data_points = 10
        
        print("🔧 Calculando CLI...")
        cli_data = cli_calculator.calculate_cli(economic_data)
        
        if cli_data.empty:
            print("❌ CLI vazio!")
            return None
        
        print(f"✅ CLI calculado: {len(cli_data)} pontos")
        print(f"   Colunas: {list(cli_data.columns)}")
        
        # Verificar valores
        print("\n📊 Primeiros 5 valores do CLI:")
        print(cli_data.head())
        
        print("\n📊 Últimos 5 valores do CLI:")
        print(cli_data.tail())
        
        # Verificar se há NaN
        print(f"\n🔍 Verificação de NaN:")
        for col in cli_data.columns:
            nan_count = cli_data[col].isna().sum()
            print(f"   {col}: {nan_count} NaN values")
        
        return cli_data
        
    except Exception as e:
        print(f"❌ Erro no cálculo do CLI: {e}")
        import traceback
        traceback.print_exc()
        return None

def debug_signal_generation(cli_data):
    """Debug da geração de sinais"""
    print("\n📈 DEBUG: Geração de Sinais")
    print("=" * 35)
    
    try:
        if cli_data is None or cli_data.empty:
            print("❌ Dados CLI não disponíveis")
            return None
        
        # Inicializar gerador de sinais
        signal_generator = SignalGenerator()
        
        print("🔧 Gerando sinais...")
        signals_data = signal_generator.generate_signals(cli_data)
        
        if signals_data.empty:
            print("❌ Sinais vazios!")
            return None
        
        print(f"✅ Sinais gerados: {len(signals_data)} pontos")
        print(f"   Colunas: {list(signals_data.columns)}")
        
        # Verificar valores
        print("\n📊 Primeiros 5 sinais:")
        print(signals_data.head())
        
        print("\n📊 Últimos 5 sinais:")
        print(signals_data.tail())
        
        # Verificar tipos de sinal
        if 'signal_type' in signals_data.columns:
            signal_counts = signals_data['signal_type'].value_counts()
            print(f"\n📊 Contagem de sinais:")
            for signal_type, count in signal_counts.items():
                print(f"   {signal_type}: {count}")
        
        # Verificar se há NaN
        print(f"\n🔍 Verificação de NaN:")
        for col in signals_data.columns:
            nan_count = signals_data[col].isna().sum()
            print(f"   {col}: {nan_count} NaN values")
        
        return signals_data
        
    except Exception as e:
        print(f"❌ Erro na geração de sinais: {e}")
        import traceback
        traceback.print_exc()
        return None

def debug_trading_simulation(signals_data):
    """Debug da simulação de trading"""
    print("\n💰 DEBUG: Simulação de Trading")
    print("=" * 40)
    
    try:
        if signals_data is None or signals_data.empty:
            print("❌ Dados de sinais não disponíveis")
            return None
        
        # Configurações
        initial_capital = 100000.0
        transaction_cost = 0.001
        
        print(f"🔧 Configurações:")
        print(f"   Capital inicial: R$ {initial_capital:,.2f}")
        print(f"   Custo transação: {transaction_cost:.1%}")
        
        # Filtrar sinais válidos
        valid_signals = signals_data[
            signals_data['signal_type'].isin(['BUY', 'SELL'])
        ].copy()
        
        print(f"📊 Sinais válidos: {len(valid_signals)}")
        
        if valid_signals.empty:
            print("❌ Nenhum sinal válido para trading")
            return None
        
        # Simular trading
        portfolio_value = initial_capital
        cash = initial_capital
        position = 0.0
        
        trades = []
        portfolio_values = []
        
        print(f"\n🔧 Simulando {len(valid_signals)} sinais...")
        
        for i, (idx, signal_row) in enumerate(valid_signals.iterrows()):
            signal_type = signal_row['signal_type']
            signal_strength = signal_row['signal_strength']
            
            print(f"   Sinal {i+1}: {signal_type} (força: {signal_strength})")
            
            # Calcular tamanho da posição
            if signal_type == 'BUY':
                target_position = min(1.0, signal_strength / 5.0)  # Máximo 100%
            elif signal_type == 'SELL':
                target_position = 0.0  # SELL = sair completamente
            else:
                continue
            
            position_change = target_position - position
            
            print(f"     Posição atual: {position:.3f}, Target: {target_position:.3f}, Change: {position_change:.3f}")
            
            if abs(position_change) > 0.001:  # Reduzir threshold para mais trades
                trade_value = abs(position_change) * portfolio_value
                transaction_cost_amount = trade_value * transaction_cost
                
                position = target_position
                cash = cash - (position_change * portfolio_value) - transaction_cost_amount
                portfolio_value = cash + (position * portfolio_value)
                
                trade = {
                    'date': idx,
                    'signal_type': signal_type,
                    'signal_strength': signal_strength,
                    'position_change': position_change,
                    'trade_value': trade_value,
                    'portfolio_value': portfolio_value
                }
                
                trades.append(trade)
                print(f"     Trade: {position_change:.2%} -> Portfolio: R$ {portfolio_value:,.2f}")
            
            portfolio_values.append({
                'date': idx,
                'portfolio_value': portfolio_value,
                'position': position
            })
        
        print(f"\n✅ Simulação concluída:")
        print(f"   Trades executados: {len(trades)}")
        print(f"   Valor final: R$ {portfolio_value:,.2f}")
        print(f"   Retorno: {((portfolio_value - initial_capital) / initial_capital):.2%}")
        
        return {
            'trades': trades,
            'portfolio_values': portfolio_values,
            'final_value': portfolio_value,
            'total_return': (portfolio_value - initial_capital) / initial_capital
        }
        
    except Exception as e:
        print(f"❌ Erro na simulação de trading: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal de debug"""
    print("🐛 DEBUG DO BACKTESTING - PASSO A PASSO")
    print("=" * 50)
    
    # 1. Debug do cálculo do CLI
    cli_data = debug_cli_calculation()
    
    if cli_data is None:
        print("\n❌ Falha no cálculo do CLI - parando debug")
        return False
    
    # 2. Debug da geração de sinais
    signals_data = debug_signal_generation(cli_data)
    
    if signals_data is None:
        print("\n❌ Falha na geração de sinais - parando debug")
        return False
    
    # 3. Debug da simulação de trading
    trading_result = debug_trading_simulation(signals_data)
    
    if trading_result is None:
        print("\n❌ Falha na simulação de trading - parando debug")
        return False
    
    # 4. Resumo final
    print("\n🎯 RESUMO DO DEBUG")
    print("=" * 25)
    print(f"✅ CLI calculado: {len(cli_data)} pontos")
    print(f"✅ Sinais gerados: {len(signals_data)} pontos")
    print(f"✅ Trades executados: {len(trading_result['trades'])}")
    print(f"✅ Retorno total: {trading_result['total_return']:.2%}")
    
    print("\n🎉 DEBUG CONCLUÍDO COM SUCESSO!")
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Debug bem-sucedido!")
        exit(0)
    else:
        print("\n❌ Debug falhou!")
        exit(1)
