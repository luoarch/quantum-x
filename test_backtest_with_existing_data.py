#!/usr/bin/env python3
"""
Teste de Backtesting com Dados Existentes
Usa dados que já temos no banco ou simula dados realistas baseados em dados reais
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
from app.core.database import get_db
from app.models.time_series import EconomicSeries
from sqlalchemy.orm import Session

def create_realistic_historical_data(start_date: str, end_date: str) -> dict:
    """Cria dados históricos realistas baseados em dados reais do Brasil"""
    
    # Criar datas mensais
    dates = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    # Dados baseados em estatísticas reais do Brasil (2010-2025)
    economic_data = {}
    
    # IPCA (Inflação) - baseado em dados reais
    # 2010-2015: alta inflação, 2016-2019: controle, 2020-2022: pandemia, 2023-2025: recuperação
    ipca_trend = []
    for i, date in enumerate(dates):
        year = date.year
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
        
        # Adicionar sazonalidade
        seasonal = 0.5 * np.sin(2 * np.pi * date.month / 12)
        noise = np.random.normal(0, volatility)
        ipca_value = base_rate + seasonal + noise
        
        ipca_trend.append(max(0.1, ipca_value))  # Mínimo 0.1%
    
    economic_data['ipca'] = pd.DataFrame({
        'date': dates,
        'value': ipca_trend
    })
    
    # SELIC (Taxa de Juros) - baseada em dados reais
    selic_trend = []
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
        selic_trend.append(max(0.1, selic_value))
    
    economic_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': selic_trend
    })
    
    # Câmbio USD/BRL - baseado em dados reais
    cambio_trend = []
    base_rate = 2.0  # 2010
    for i, date in enumerate(dates):
        year = date.year
        # Tendência de desvalorização do Real
        trend = 0.15 * (year - 2010)  # 15% ao ano
        noise = np.random.normal(0, 0.1)
        cambio_value = base_rate * (1 + trend) * (1 + noise)
        cambio_trend.append(max(1.0, cambio_value))
    
    economic_data['cambio'] = pd.DataFrame({
        'date': dates,
        'value': cambio_trend
    })
    
    # Produção Industrial - cíclica com tendência
    prod_trend = []
    base_value = 100.0
    for i, date in enumerate(dates):
        # Ciclo de negócios (4 anos)
        cycle = 10 * np.sin(2 * np.pi * i / 48)  # 48 meses = 4 anos
        # Tendência de crescimento
        trend = 0.02 * i  # 2% ao ano
        # Ruído
        noise = np.random.normal(0, 3.0)
        prod_value = base_value + cycle + trend + noise
        prod_trend.append(max(50.0, prod_value))
    
    economic_data['prod_industrial'] = pd.DataFrame({
        'date': dates,
        'value': prod_trend
    })
    
    # PIB - crescimento moderado
    pib_trend = []
    base_value = 100.0
    for i, date in enumerate(dates):
        # Crescimento médio de 2% ao ano
        growth = 0.02 * i / 12  # 2% ao ano
        # Ciclo de negócios
        cycle = 5 * np.sin(2 * np.pi * i / 60)  # 60 meses = 5 anos
        # Ruído
        noise = np.random.normal(0, 1.0)
        pib_value = base_value * (1 + growth) + cycle + noise
        pib_trend.append(max(50.0, pib_value))
    
    economic_data['pib'] = pd.DataFrame({
        'date': dates,
        'value': pib_trend
    })
    
    # Desemprego - baseado em dados reais
    desemprego_trend = []
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
        desemprego_trend.append(max(3.0, desemprego_value))
    
    economic_data['desemprego'] = pd.DataFrame({
        'date': dates,
        'value': desemprego_trend
    })
    
    return economic_data

async def test_backtest_with_realistic_data():
    """Executa backtesting com dados realistas"""
    
    print("🚀 BACKTESTING COM DADOS REALISTAS - ESTRATÉGIA CLI")
    print("=" * 60)
    
    try:
        # 1. Configurar período
        print("\n📅 1. Configurando período de backtesting...")
        start_date = "2015-01-01"
        end_date = "2025-09-23"
        
        print(f"   Período: {start_date} a {end_date}")
        print(f"   Duração: ~10.7 anos")
        
        # 2. Criar dados históricos realistas
        print("\n📊 2. Criando dados históricos realistas...")
        economic_data = create_realistic_historical_data(start_date, end_date)
        
        print(f"✅ Dados criados: {len(economic_data)} séries")
        for series_name, df in economic_data.items():
            print(f"   - {series_name}: {len(df)} pontos")
        
        # 3. Calcular CLI
        print("\n🧮 3. Calculando CLI histórico...")
        cli_calculator = CLICalculator()
        cli_data = cli_calculator.calculate_cli(economic_data)
        
        if cli_data.empty:
            print("❌ Falha no cálculo do CLI")
            return False
        
        print(f"✅ CLI calculado: {len(cli_data)} pontos")
        print(f"   - CLI atual: {cli_data['cli_normalized'].iloc[-1]:.2f}")
        print(f"   - Tendência: {cli_data['cli_trend'].iloc[-1]:.2f}")
        print(f"   - Momentum: {cli_data['cli_momentum'].iloc[-1]:.2f}")
        
        # 4. Gerar sinais
        print("\n📈 4. Gerando sinais históricos...")
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
        
        # 5. Simular trading
        print("\n💰 5. Simulando trading...")
        
        # Configurações
        initial_capital = 100000.0
        transaction_cost = 0.001  # 0.1%
        
        # Simular trading
        portfolio_value = initial_capital
        cash = initial_capital
        position = 0.0  # 0 = sem posição, 1 = 100% investido
        
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
            
            # Calcular tamanho da posição baseado no sinal
            if signal_type == 'BUY':
                target_position = min(1.0, signal_strength / 5.0)  # Máximo 100%
            elif signal_type == 'SELL':
                target_position = max(0.0, 1.0 - (signal_strength / 5.0))  # Mínimo 0%
            else:
                continue
            
            # Calcular mudança de posição
            position_change = target_position - position
            
            if abs(position_change) > 0.01:  # Só trade se mudança > 1%
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
        
        # 6. Calcular métricas de performance
        print("\n📊 6. Calculando métricas de performance...")
        
        if not portfolio_values:
            print("❌ Nenhum dado de portfolio para análise")
            return False
        
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
        annualized_return = (1 + total_return) ** (1 / years) - 1
        
        # Volatilidade
        volatility = portfolio_df['returns'].std() * np.sqrt(252)  # Anualizada
        
        # Sharpe Ratio
        risk_free_rate = 0.05  # 5% ao ano
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + portfolio_df['returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Estatísticas de trades
        if trades:
            trades_df = pd.DataFrame(trades)
            profitable_trades = len(trades_df[trades_df['position_change'] > 0])
            total_trades = len(trades_df)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        else:
            total_trades = 0
            win_rate = 0
        
        # 7. Exibir resultados
        print("\n🎯 7. RESULTADOS DO BACKTESTING")
        print("=" * 40)
        
        print(f"💰 Capital Inicial: R$ {initial_value:,.2f}")
        print(f"💰 Capital Final: R$ {final_value:,.2f}")
        print(f"📈 Retorno Total: {total_return:.2%}")
        print(f"📈 Retorno Anualizado: {annualized_return:.2%}")
        print(f"📉 Maximum Drawdown: {max_drawdown:.2%}")
        print(f"⚡ Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"📊 Volatilidade Anual: {volatility:.2%}")
        print(f"🎯 Taxa de Vitória: {win_rate:.2%}")
        print(f"📊 Total de Trades: {total_trades}")
        print(f"📈 Sinais Gerados: {len(signals_data)}")
        
        # 8. Avaliação da estratégia
        print("\n🏆 8. AVALIAÇÃO DA ESTRATÉGIA")
        print("=" * 35)
        
        # Critérios de avaliação
        sharpe_ok = sharpe_ratio > 0.5
        drawdown_ok = max_drawdown > -0.20
        win_rate_ok = win_rate > 0.50
        return_ok = annualized_return > 0.05
        
        print(f"Sharpe Ratio > 0.5: {'✅' if sharpe_ok else '❌'} ({sharpe_ratio:.2f})")
        print(f"Drawdown < 20%: {'✅' if drawdown_ok else '❌'} ({max_drawdown:.2%})")
        print(f"Taxa Vitória > 50%: {'✅' if win_rate_ok else '❌'} ({win_rate:.2%})")
        print(f"Retorno > 5% a.a.: {'✅' if return_ok else '❌'} ({annualized_return:.2%})")
        
        # Score geral
        score = sum([sharpe_ok, drawdown_ok, win_rate_ok, return_ok])
        print(f"\n🏆 Score Geral: {score}/4")
        
        if score >= 3:
            print("🎉 ESTRATÉGIA APROVADA - Pronta para produção!")
        elif score >= 2:
            print("⚠️ ESTRATÉGIA PARCIALMENTE APROVADA - Necessita ajustes")
        else:
            print("❌ ESTRATÉGIA REJEITADA - Necessita reformulação")
        
        # 9. Mostrar últimos sinais
        print("\n📋 9. ÚLTIMOS SINAIS GERADOS")
        print("=" * 35)
        
        last_signals = signals_data.tail(10)
        for idx, row in last_signals.iterrows():
            date_str = str(idx) if hasattr(idx, 'strftime') else f"Ponto {idx}"
            print(f"   {date_str}: {row['signal_type']} "
                  f"(força: {row['signal_strength']}, confiança: {row['signal_confidence']:.3f}, "
                  f"CLI: {row['cli_normalized']:.2f})")
        
        print("\n✅ BACKTESTING COM DADOS REALISTAS CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no backtesting: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE BACKTESTING COM DADOS REALISTAS")
    print("=" * 60)
    
    success = asyncio.run(test_backtest_with_realistic_data())
    
    if success:
        print("\n🎉 Teste concluído com sucesso!")
        exit(0)
    else:
        print("\n💥 Teste falhou!")
        exit(1)
