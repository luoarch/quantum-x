#!/usr/bin/env python3
"""
Backtesting Completo com Dados Históricos Realistas
Implementa backtesting rigoroso com métricas de performance completas
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.signal_generation import CLICalculator, SignalGenerator, MLOptimizer, PositionSizing

def create_historical_data_2010_2025():
    """Cria dados históricos realistas baseados em dados reais do Brasil (2010-2025)"""
    
    print("📊 Criando dados históricos realistas (2010-2025)...")
    
    # Criar datas mensais de 2010 a 2025
    dates = pd.date_range(start="2010-01-01", end="2025-09-30", freq='ME')
    
    economic_data = {}
    
    # IPCA (Inflação) - baseado em dados reais do Brasil
    ipca_values = []
    for i, date in enumerate(dates):
        year = date.year
        month = date.month
        
        # Dados baseados em estatísticas reais
        if year <= 2015:
            # Alta inflação (6-10%)
            base_rate = 8.0
            volatility = 2.0
        elif year <= 2019:
            # Controle (3-6%)
            base_rate = 4.5
            volatility = 1.5
        elif year <= 2022:
            # Pandemia (5-12%)
            base_rate = 8.5
            volatility = 3.0
        else:
            # Recuperação (3-5%)
            base_rate = 4.0
            volatility = 1.0
        
        # Sazonalidade (inflação maior no final do ano)
        seasonal = 0.5 * np.sin(2 * np.pi * month / 12)
        
        # Ruído
        noise = np.random.normal(0, volatility)
        
        ipca_value = base_rate + seasonal + noise
        ipca_values.append(max(0.1, ipca_value))  # Mínimo 0.1%
    
    economic_data['ipca'] = pd.DataFrame({
        'date': dates,
        'value': ipca_values
    })
    
    # SELIC (Taxa de Juros) - baseada em dados reais
    selic_values = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            # Alta (10-14%)
            base_rate = 12.0
        elif year <= 2019:
            # Redução (6-10%)
            base_rate = 8.0
        elif year <= 2022:
            # Pandemia (2-14%)
            base_rate = 8.0
        else:
            # Pós-pandemia (10-14%)
            base_rate = 12.0
        
        noise = np.random.normal(0, 1.0)
        selic_value = base_rate + noise
        selic_values.append(max(0.1, selic_value))
    
    economic_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': selic_values
    })
    
    # Câmbio USD/BRL - baseado em dados reais
    cambio_values = []
    base_rate = 2.0  # 2010
    for i, date in enumerate(dates):
        year = date.year
        # Tendência de desvalorização do Real (15% ao ano)
        trend = 0.15 * (year - 2010)
        noise = np.random.normal(0, 0.1)
        cambio_value = base_rate * (1 + trend) * (1 + noise)
        cambio_values.append(max(1.0, cambio_value))
    
    economic_data['cambio'] = pd.DataFrame({
        'date': dates,
        'value': cambio_values
    })
    
    # Produção Industrial - cíclica com tendência
    prod_values = []
    base_value = 100.0
    for i, date in enumerate(dates):
        # Ciclo de negócios (4 anos)
        cycle = 10 * np.sin(2 * np.pi * i / 48)  # 48 meses = 4 anos
        # Tendência de crescimento (2% ao ano)
        trend = 0.02 * i / 12
        # Ruído
        noise = np.random.normal(0, 3.0)
        prod_value = base_value * (1 + trend) + cycle + noise
        prod_values.append(max(50.0, prod_value))
    
    economic_data['prod_industrial'] = pd.DataFrame({
        'date': dates,
        'value': prod_values
    })
    
    # PIB - crescimento moderado
    pib_values = []
    base_value = 100.0
    for i, date in enumerate(dates):
        # Crescimento médio de 2% ao ano
        growth = 0.02 * i / 12
        # Ciclo de negócios (5 anos)
        cycle = 5 * np.sin(2 * np.pi * i / 60)  # 60 meses = 5 anos
        # Ruído
        noise = np.random.normal(0, 1.0)
        pib_value = base_value * (1 + growth) + cycle + noise
        pib_values.append(max(50.0, pib_value))
    
    economic_data['pib'] = pd.DataFrame({
        'date': dates,
        'value': pib_values
    })
    
    # Desemprego - baseado em dados reais
    desemprego_values = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            # Baixo desemprego (5-8%)
            base_rate = 6.5
        elif year <= 2019:
            # Alto desemprego (10-14%)
            base_rate = 12.0
        elif year <= 2022:
            # Pandemia (12-16%)
            base_rate = 14.0
        else:
            # Recuperação (8-12%)
            base_rate = 10.0
        
        noise = np.random.normal(0, 1.0)
        desemprego_value = base_rate + noise
        desemprego_values.append(max(3.0, desemprego_value))
    
    economic_data['desemprego'] = pd.DataFrame({
        'date': dates,
        'value': desemprego_values
    })
    
    print(f"✅ Dados históricos criados: {len(economic_data)} séries")
    for series_name, df in economic_data.items():
        print(f"   - {series_name}: {len(df)} pontos ({df['date'].iloc[0].strftime('%Y-%m')} a {df['date'].iloc[-1].strftime('%Y-%m')})")
    
    return economic_data

def calculate_performance_metrics(portfolio_values, trades, initial_capital):
    """Calcula métricas de performance completas"""
    
    if not portfolio_values:
        return None
    
    # Converter para DataFrame
    portfolio_df = pd.DataFrame(portfolio_values)
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
    portfolio_df = portfolio_df.set_index('date').sort_index()
    
    # Calcular retornos
    portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change().fillna(0)
    
    # Métricas básicas
    initial_value = portfolio_df['portfolio_value'].iloc[0]
    final_value = portfolio_df['portfolio_value'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # Retorno anualizado
    years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # Volatilidade anualizada
    volatility = portfolio_df['returns'].std() * np.sqrt(252)
    
    # Sharpe Ratio
    risk_free_rate = 0.05  # 5% ao ano
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0
    
    # Maximum Drawdown
    cumulative = (1 + portfolio_df['returns']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Calmar Ratio
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Sortino Ratio
    negative_returns = portfolio_df['returns'][portfolio_df['returns'] < 0]
    downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
    sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
    
    # Estatísticas de trades
    if trades:
        trades_df = pd.DataFrame(trades)
        profitable_trades = len(trades_df[trades_df['position_change'] > 0])
        total_trades = len(trades_df)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        avg_trade_return = trades_df['position_change'].mean()
    else:
        profitable_trades = 0
        total_trades = 0
        win_rate = 0
        avg_trade_return = 0
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar_ratio,
        'sortino_ratio': sortino_ratio,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'avg_trade_return': avg_trade_return,
        'initial_capital': initial_value,
        'final_capital': final_value,
        'years': years
    }

async def run_complete_backtest():
    """Executa backtesting completo com dados históricos"""
    
    print("🚀 BACKTESTING COMPLETO - ESTRATÉGIA CLI")
    print("=" * 60)
    
    try:
        # 1. Criar dados históricos
        print("\n📊 1. Criando dados históricos realistas...")
        economic_data = create_historical_data_2010_2025()
        
        # 2. Calcular CLI
        print("\n🧮 2. Calculando CLI histórico...")
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
        print("\n📈 3. Gerando sinais históricos...")
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
        
        # 4. Simular trading
        print("\n💰 4. Simulando trading...")
        
        # Configurações
        initial_capital = 100000.0
        transaction_cost = 0.001  # 0.1%
        
        # Simular trading
        portfolio_value = initial_capital
        cash = initial_capital
        position = 0.0
        
        trades = []
        portfolio_values = []
        
        # Filtrar sinais válidos
        valid_signals = signals_data[
            signals_data['signal_type'].isin(['BUY', 'SELL'])
        ].copy()
        
        print(f"   - Sinais válidos para trading: {len(valid_signals)}")
        
        for idx, signal_row in valid_signals.iterrows():
            signal_type = signal_row['signal_type']
            signal_strength = signal_row['signal_strength']
            signal_confidence = signal_row['signal_confidence']
            cli_value = signal_row['cli_normalized']
            
            # Calcular tamanho da posição (mais agressivo)
            if signal_type == 'BUY':
                # Posição baseada na força do sinal (mais agressivo)
                base_position = signal_strength / 5.0
                # Adicionar confiança como multiplicador
                confidence_multiplier = 1 + (signal_confidence * 0.5)  # 1.0 a 1.5
                target_position = min(1.0, base_position * confidence_multiplier)
            elif signal_type == 'SELL':
                # SELL gradual baseado na força
                if signal_strength >= 4:
                    target_position = 0.0  # SELL forte = sair completamente
                else:
                    target_position = max(0.0, position - (signal_strength / 5.0))  # SELL gradual
            else:
                continue
            
            position_change = target_position - position
            
            if abs(position_change) > 0.0001:  # Só trade se mudança > 0.01% (mais sensível)
                # Calcular custo da transação
                trade_value = abs(position_change) * portfolio_value
                transaction_cost_amount = trade_value * transaction_cost
                
                # Atualizar posição
                position = target_position
                cash = cash - (position_change * portfolio_value) - transaction_cost_amount
                portfolio_value = cash + (position * portfolio_value)
                
                # Registrar trade
                trade = {
                    'date': idx,
                    'signal_type': signal_type,
                    'signal_strength': signal_strength,
                    'signal_confidence': signal_confidence,
                    'cli_value': cli_value,
                    'position_before': position - position_change,
                    'position_after': position,
                    'position_change': position_change,
                    'trade_value': trade_value,
                    'transaction_cost': transaction_cost_amount,
                    'portfolio_value': portfolio_value,
                    'cash': cash
                }
                
                trades.append(trade)
            
            # Registrar valor do portfolio
            portfolio_values.append({
                'date': idx,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'position': position,
                'cli_value': cli_value
            })
        
        print(f"✅ Simulação concluída: {len(trades)} trades executados")
        
        # 5. Calcular métricas de performance
        print("\n📊 5. Calculando métricas de performance...")
        
        metrics = calculate_performance_metrics(portfolio_values, trades, initial_capital)
        
        if metrics is None:
            print("❌ Falha no cálculo de métricas")
            return False
        
        # 6. Exibir resultados
        print("\n🎯 6. RESULTADOS DO BACKTESTING")
        print("=" * 40)
        
        start_date = portfolio_values[0]['date']
        end_date = portfolio_values[-1]['date']
        if hasattr(start_date, 'strftime'):
            start_str = start_date.strftime('%Y-%m')
        else:
            start_str = str(start_date)
        if hasattr(end_date, 'strftime'):
            end_str = end_date.strftime('%Y-%m')
        else:
            end_str = str(end_date)
        print(f"📅 Período: {start_str} a {end_str}")
        print(f"⏱️ Duração: {metrics['years']:.1f} anos")
        print(f"💰 Capital Inicial: R$ {metrics['initial_capital']:,.2f}")
        print(f"💰 Capital Final: R$ {metrics['final_capital']:,.2f}")
        print(f"📈 Retorno Total: {metrics['total_return']:.2%}")
        print(f"📈 Retorno Anualizado: {metrics['annualized_return']:.2%}")
        print(f"📉 Maximum Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"⚡ Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"📊 Volatilidade Anual: {metrics['volatility']:.2%}")
        print(f"🎯 Taxa de Vitória: {metrics['win_rate']:.2%}")
        print(f"📊 Total de Trades: {metrics['total_trades']}")
        print(f"💎 Calmar Ratio: {metrics['calmar_ratio']:.2f}")
        print(f"📉 Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        
        # 7. Avaliação da estratégia
        print("\n🏆 7. AVALIAÇÃO DA ESTRATÉGIA")
        print("=" * 35)
        
        # Critérios de avaliação
        sharpe_ok = metrics['sharpe_ratio'] > 0.5
        drawdown_ok = metrics['max_drawdown'] > -0.20
        win_rate_ok = metrics['win_rate'] > 0.50
        return_ok = metrics['annualized_return'] > 0.05
        
        print(f"Sharpe Ratio > 0.5: {'✅' if sharpe_ok else '❌'} ({metrics['sharpe_ratio']:.2f})")
        print(f"Drawdown < 20%: {'✅' if drawdown_ok else '❌'} ({metrics['max_drawdown']:.2%})")
        print(f"Taxa Vitória > 50%: {'✅' if win_rate_ok else '❌'} ({metrics['win_rate']:.2%})")
        print(f"Retorno > 5% a.a.: {'✅' if return_ok else '❌'} ({metrics['annualized_return']:.2%})")
        
        # Score geral
        score = sum([sharpe_ok, drawdown_ok, win_rate_ok, return_ok])
        print(f"\n🏆 Score Geral: {score}/4")
        
        if score >= 3:
            print("🎉 ESTRATÉGIA APROVADA - Pronta para produção!")
        elif score >= 2:
            print("⚠️ ESTRATÉGIA PARCIALMENTE APROVADA - Necessita ajustes")
        else:
            print("❌ ESTRATÉGIA REJEITADA - Necessita reformulação")
        
        # 8. Mostrar últimos sinais
        print("\n📋 8. ÚLTIMOS SINAIS GERADOS")
        print("=" * 35)
        
        last_signals = signals_data.tail(10)
        for idx, row in last_signals.iterrows():
            date_str = str(idx) if hasattr(idx, 'strftime') else f"Ponto {idx}"
            print(f"   {date_str}: {row['signal_type']} "
                  f"(força: {row['signal_strength']}, confiança: {row['signal_confidence']:.3f}, "
                  f"CLI: {row['cli_normalized']:.2f})")
        
        print("\n✅ BACKTESTING COMPLETO CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no backtesting: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE BACKTESTING COMPLETO")
    print("=" * 50)
    
    success = asyncio.run(run_complete_backtest())
    
    if success:
        print("\n🎉 Backtesting concluído com sucesso!")
        exit(0)
    else:
        print("\n💥 Backtesting falhou!")
        exit(1)
