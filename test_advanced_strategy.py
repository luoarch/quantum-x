#!/usr/bin/env python3
"""
Teste da Estratégia Avançada - Markov-Switching + HRP + Curva de Juros
Implementa metodologias de última geração para geração de alfa
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator
from app.services.signal_generation.markov_switching_model import MarkovSwitchingModel
from app.services.signal_generation.hierarchical_risk_parity import HierarchicalRiskParity
from app.services.signal_generation.yield_curve_indicators import YieldCurveIndicators

def create_advanced_test_data():
    """Cria dados de teste para a estratégia avançada"""
    
    print("📊 Criando dados de teste para estratégia avançada...")
    
    # Criar datas mensais de 2010 a 2025
    dates = pd.date_range(start="2010-01-01", end="2025-09-30", freq='ME')
    
    # Dados econômicos
    economic_data = {}
    
    # IPCA com ciclos realistas
    ipca_values = []
    for i, date in enumerate(dates):
        year = date.year
        month = date.month
        
        # Ciclo de inflação baseado em dados reais
        if year <= 2015:
            base_rate = 8.0
            volatility = 2.0
        elif year <= 2019:
            base_rate = 4.5
            volatility = 1.5
        elif year <= 2022:
            base_rate = 8.5
            volatility = 3.0
        else:
            base_rate = 4.0
            volatility = 1.0
        
        # Sazonalidade
        seasonal = 0.5 * np.sin(2 * np.pi * month / 12)
        noise = np.random.normal(0, volatility)
        ipca_value = base_rate + seasonal + noise
        ipca_values.append(max(0.1, ipca_value))
    
    economic_data['ipca'] = pd.DataFrame({
        'date': dates,
        'value': ipca_values
    })
    
    # SELIC com ciclos de política monetária
    selic_values = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            base_rate = 12.0
        elif year <= 2019:
            base_rate = 8.0
        elif year <= 2022:
            base_rate = 8.0
        else:
            base_rate = 12.0
        
        noise = np.random.normal(0, 1.0)
        selic_value = base_rate + noise
        selic_values.append(max(0.1, selic_value))
    
    economic_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': selic_values
    })
    
    # Câmbio com tendência de desvalorização
    cambio_values = []
    base_rate = 2.0
    for i, date in enumerate(dates):
        year = date.year
        trend = 0.15 * (year - 2010)
        noise = np.random.normal(0, 0.1)
        cambio_value = base_rate * (1 + trend) * (1 + noise)
        cambio_values.append(max(1.0, cambio_value))
    
    economic_data['cambio'] = pd.DataFrame({
        'date': dates,
        'value': cambio_values
    })
    
    # Produção Industrial cíclica
    prod_values = []
    base_value = 100.0
    for i, date in enumerate(dates):
        cycle = 10 * np.sin(2 * np.pi * i / 48)  # 4 anos
        trend = 0.02 * i / 12
        noise = np.random.normal(0, 3.0)
        prod_value = base_value * (1 + trend) + cycle + noise
        prod_values.append(max(50.0, prod_value))
    
    economic_data['prod_industrial'] = pd.DataFrame({
        'date': dates,
        'value': prod_values
    })
    
    # PIB com crescimento moderado
    pib_values = []
    base_value = 100.0
    for i, date in enumerate(dates):
        growth = 0.02 * i / 12
        cycle = 5 * np.sin(2 * np.pi * i / 60)  # 5 anos
        noise = np.random.normal(0, 1.0)
        pib_value = base_value * (1 + growth) + cycle + noise
        pib_values.append(max(50.0, pib_value))
    
    economic_data['pib'] = pd.DataFrame({
        'date': dates,
        'value': pib_values
    })
    
    # Desemprego com ciclos de mercado de trabalho
    desemprego_values = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            base_rate = 6.5
        elif year <= 2019:
            base_rate = 12.0
        elif year <= 2022:
            base_rate = 14.0
        else:
            base_rate = 10.0
        
        noise = np.random.normal(0, 1.0)
        desemprego_value = base_rate + noise
        desemprego_values.append(max(3.0, desemprego_value))
    
    economic_data['desemprego'] = pd.DataFrame({
        'date': dates,
        'value': desemprego_values
    })
    
    # Criar CLI simples
    cli_values = []
    for i, date in enumerate(dates):
        # CLI baseado em múltiplos indicadores
        ipca_contrib = -ipca_values[i] / 10  # Inflação alta = CLI baixo
        selic_contrib = -selic_values[i] / 20  # Juros altos = CLI baixo
        prod_contrib = (prod_values[i] - 100) / 100  # Produção alta = CLI alto
        pib_contrib = (pib_values[i] - 100) / 100  # PIB alto = CLI alto
        desemprego_contrib = -(desemprego_values[i] - 10) / 10  # Desemprego alto = CLI baixo
        
        cli_value = 100 + ipca_contrib + selic_contrib + prod_contrib + pib_contrib + desemprego_contrib
        cli_values.append(cli_value)
    
    economic_data['cli_normalized'] = pd.DataFrame({
        'date': dates,
        'value': cli_values
    })
    
    # Dados de ativos
    asset_returns = pd.DataFrame(index=dates)
    
    # Tesouro IPCA+ com retorno realista
    tesouro_returns = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            annual_return = 0.12
        elif year <= 2019:
            annual_return = 0.08
        elif year <= 2022:
            annual_return = 0.15
        else:
            annual_return = 0.10
        
        monthly_return = annual_return / 12 + np.random.normal(0, 0.02)
        tesouro_returns.append(monthly_return)
    
    asset_returns['TESOURO_IPCA'] = tesouro_returns
    
    # BOVA11 com retorno realista
    bova11_returns = []
    for i, date in enumerate(dates):
        year = date.year
        
        if year <= 2015:
            annual_return = 0.05
        elif year <= 2019:
            annual_return = 0.15
        elif year <= 2022:
            annual_return = 0.08
        else:
            annual_return = 0.12
        
        monthly_return = annual_return / 12 + np.random.normal(0, 0.05)
        bova11_returns.append(monthly_return)
    
    asset_returns['BOVA11'] = bova11_returns
    
    # Dados de curva de juros (simulados)
    yield_data = {}
    
    # SELIC
    yield_data['selic'] = pd.DataFrame({
        'date': dates,
        'value': selic_values
    })
    
    # Swap DI 12M
    swap_12m_values = []
    for i, date in enumerate(dates):
        base_rate = selic_values[i]
        spread = np.random.normal(0.5, 0.2)
        swap_12m_values.append(base_rate + spread)
    
    yield_data['swap_di_12m'] = pd.DataFrame({
        'date': dates,
        'value': swap_12m_values
    })
    
    # Tesouro 2Y
    tesouro_2y_values = []
    for i, date in enumerate(dates):
        base_rate = selic_values[i]
        spread = np.random.normal(1.0, 0.3)
        tesouro_2y_values.append(base_rate + spread)
    
    yield_data['tesouro_2y'] = pd.DataFrame({
        'date': dates,
        'value': tesouro_2y_values
    })
    
    # Tesouro 10Y
    tesouro_10y_values = []
    for i, date in enumerate(dates):
        base_rate = selic_values[i]
        spread = np.random.normal(2.0, 0.5)
        tesouro_10y_values.append(base_rate + spread)
    
    yield_data['tesouro_10y'] = pd.DataFrame({
        'date': dates,
        'value': tesouro_10y_values
    })
    
    print(f"✅ Dados criados:")
    print(f"   - Econômicos: {len(economic_data)} séries")
    print(f"   - Ativos: {len(asset_returns.columns)} ativos")
    print(f"   - Curva de juros: {len(yield_data)} séries")
    
    return economic_data, asset_returns, yield_data

async def test_advanced_strategy():
    """Testa a estratégia avançada"""
    
    print("🚀 TESTE DA ESTRATÉGIA AVANÇADA")
    print("=" * 50)
    
    try:
        # 1. Criar dados de teste
        print("\n📊 1. Criando dados de teste...")
        economic_data, asset_returns, yield_data = create_advanced_test_data()
        
        # 2. Inicializar gerador de sinais probabilísticos
        print("\n🧠 2. Inicializando gerador de sinais probabilísticos...")
        signal_generator = ProbabilisticSignalGenerator(
            confidence_threshold=0.8,
            regime_confirmation_months=2,
            spread_threshold=0.5
        )
        
        # 3. Gerar sinais
        print("\n📈 3. Gerando sinais probabilísticos...")
        results = signal_generator.generate_signals(
            economic_data, 
            asset_returns, 
            yield_data
        )
        
        if 'error' in results:
            print(f"❌ Erro na geração de sinais: {results['error']}")
            return False
        
        # 4. Exibir resultados
        print("\n🎯 4. RESULTADOS DA ESTRATÉGIA AVANÇADA")
        print("=" * 50)
        
        signals = results['signals']
        summary = results['summary']
        
        print(f"📊 Total de sinais: {summary['total_signals']}")
        print(f"📈 Sinais de compra: {summary['buy_signals']} ({summary['buy_percentage']:.1f}%)")
        print(f"📉 Sinais de venda: {summary['sell_signals']} ({summary['sell_percentage']:.1f}%)")
        print(f"⏸️ Sinais de hold: {summary['hold_signals']} ({summary['hold_percentage']:.1f}%)")
        print(f"🎯 Confiança média: {summary['avg_confidence']:.3f}")
        print(f"📊 Probabilidade média de compra: {summary['avg_buy_probability']:.3f}")
        print(f"📊 Probabilidade média de venda: {summary['avg_sell_probability']:.3f}")
        
        # 5. Resumo dos regimes
        print("\n🏛️ 5. RESUMO DOS REGIMES")
        print("=" * 30)
        
        if 'regime_summary' in summary:
            for regime, stats in summary['regime_summary'].items():
                print(f"   {regime}:")
                print(f"     - Frequência: {stats['frequency']:.1%}")
                print(f"     - Probabilidade média: {stats['avg_probability']:.3f}")
                print(f"     - Probabilidade máxima: {stats['max_probability']:.3f}")
        
        # 6. Alocação HRP
        print("\n💰 6. ALOCAÇÃO HIERARCHICAL RISK PARITY")
        print("=" * 45)
        
        if 'hrp_allocation' in summary and summary['hrp_allocation']:
            for asset, allocation in summary['hrp_allocation'].items():
                print(f"   {asset}: {allocation:.1%}")
        
        # 7. Métricas HRP
        if 'hrp_metrics' in summary and summary['hrp_metrics']:
            metrics = summary['hrp_metrics']
            print(f"\n📊 Métricas HRP:")
            print(f"   - Retorno esperado: {metrics.get('expected_return', 0):.2%}")
            print(f"   - Volatilidade: {metrics.get('volatility', 0):.2%}")
            print(f"   - Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"   - Diversificação efetiva: {metrics.get('effective_diversification', 0):.2f}")
        
        # 8. Últimos sinais
        print("\n📋 7. ÚLTIMOS SINAIS GERADOS")
        print("=" * 35)
        
        last_signals = signals.tail(10)
        for idx, row in last_signals.iterrows():
            if hasattr(idx, 'strftime'):
                date_str = idx.strftime('%Y-%m-%d')
            elif hasattr(idx, '__str__'):
                date_str = str(idx)
            else:
                date_str = f"Ponto {idx}"
            regime = row.get('most_likely_regime', 'N/A')
            confidence = row.get('regime_confidence', 0)
            buy_prob = row.get('buy_probability', 0)
            sell_prob = row.get('sell_probability', 0)
            final_signal = row.get('final_signal', 0)
            
            signal_type = "BUY" if final_signal > 0 else "SELL" if final_signal < 0 else "HOLD"
            
            print(f"   {date_str}: {signal_type} "
                  f"(Regime: {regime}, Conf: {confidence:.3f}, "
                  f"Buy: {buy_prob:.3f}, Sell: {sell_prob:.3f})")
        
        print("\n✅ ESTRATÉGIA AVANÇADA TESTADA COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste da estratégia avançada: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTE DA ESTRATÉGIA AVANÇADA")
    print("=" * 50)
    
    success = asyncio.run(test_advanced_strategy())
    
    if success:
        print("\n🎉 Teste da estratégia avançada concluído com sucesso!")
        exit(0)
    else:
        print("\n💥 Teste da estratégia avançada falhou!")
        exit(1)
