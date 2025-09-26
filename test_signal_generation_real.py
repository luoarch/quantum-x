#!/usr/bin/env python3
"""
Teste da geração de sinais com dados reais
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator
from app.services.data_sources.bacen_sgs_source import BacenSGSSource
from app.services.data_sources.fred_source import FREDSource
from app.services.data_sources.yahoo_source import YahooSource
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def collect_real_data():
    """Coleta dados reais das APIs"""
    print("📊 COLETANDO DADOS REAIS DAS APIs")
    print("=" * 50)
    
    economic_data = {}
    
    try:
        # BACEN SGS - IPCA
        print("🏦 Coletando IPCA (BACEN SGS)...")
        bacen_source = BacenSGSSource()
        ipca_data = await bacen_source.fetch_data({'name': 'ipca', 'limit': 24})
        if not ipca_data.empty:
            # Normalizar para formato esperado
            ipca_df = ipca_data[['date', 'value']].copy()
            ipca_df['date'] = pd.to_datetime(ipca_df['date'])
            ipca_df = ipca_df.set_index('date').sort_index()
            economic_data['ipca'] = ipca_df
            print(f"✅ IPCA: {len(ipca_df)} registros")
        
        # BACEN SGS - SELIC
        print("🏦 Coletando SELIC (BACEN SGS)...")
        selic_data = await bacen_source.fetch_data({'name': 'selic', 'limit': 24})
        if not selic_data.empty:
            selic_df = selic_data[['date', 'value']].copy()
            selic_df['date'] = pd.to_datetime(selic_df['date'])
            selic_df = selic_df.set_index('date').sort_index()
            economic_data['selic'] = selic_df
            print(f"✅ SELIC: {len(selic_df)} registros")
        
        # FRED - CLI
        print("🏛️ Coletando CLI (FRED)...")
        fred_source = FREDSource()
        cli_data = await fred_source.fetch_data({'country': 'BRA', 'start_year': 2022, 'end_year': 2024})
        if not cli_data.empty:
            cli_df = cli_data[['date', 'value']].copy()
            cli_df['date'] = pd.to_datetime(cli_df['date'])
            cli_df = cli_df.set_index('date').sort_index()
            economic_data['cli'] = cli_df
            print(f"✅ CLI: {len(cli_df)} registros")
        
        # Yahoo Finance - BOVA11
        print("📈 Coletando BOVA11 (Yahoo Finance)...")
        yahoo_source = YahooSource()
        bova_data = await yahoo_source.fetch_data({'symbol': 'BOVA11', 'period': '2y', 'interval': '1mo'})
        if not bova_data.empty:
            bova_df = bova_data[['date', 'value']].copy()
            bova_df['date'] = pd.to_datetime(bova_df['date'])
            bova_df = bova_df.set_index('date').sort_index()
            
            # Calcular retornos
            bova_returns = bova_df['value'].pct_change().fillna(0)
            asset_returns = pd.DataFrame({'BOVA11': bova_returns})
            print(f"✅ BOVA11: {len(asset_returns)} registros de retorno")
        else:
            asset_returns = pd.DataFrame()
            print("❌ BOVA11: Falha na coleta")
        
        # Criar retornos de renda fixa baseado na SELIC
        if 'selic' in economic_data and not economic_data['selic'].empty:
            selic_series = economic_data['selic']['value'] / 100.0
            monthly_return = (1.0 + selic_series) ** (1.0 / 12.0) - 1.0
            tesouro_returns = pd.DataFrame({'TESOURO_IPCA': monthly_return})
            
            if not asset_returns.empty:
                # Alinhar índices
                common_index = asset_returns.index.intersection(tesouro_returns.index)
                if len(common_index) > 0:
                    asset_returns = asset_returns.reindex(common_index)
                    tesouro_returns = tesouro_returns.reindex(common_index)
                    asset_returns['TESOURO_IPCA'] = tesouro_returns['TESOURO_IPCA']
                else:
                    asset_returns['TESOURO_IPCA'] = 0.0
            else:
                asset_returns = tesouro_returns
                asset_returns['BOVA11'] = 0.0
            
            print(f"✅ TESOURO_IPCA: {len(tesouro_returns)} registros de retorno")
        
        return economic_data, asset_returns
        
    except Exception as e:
        print(f"❌ Erro na coleta de dados: {e}")
        return {}, pd.DataFrame()

async def test_signal_generation():
    """Testa geração de sinais com dados reais"""
    print("\n🧠 TESTANDO GERAÇÃO DE SINAIS COM DADOS REAIS")
    print("=" * 60)
    
    try:
        # Coletar dados reais
        economic_data, asset_returns = await collect_real_data()
        
        if not economic_data or asset_returns.empty:
            print("❌ Dados insuficientes para gerar sinais")
            return False
        
        print(f"\n📊 Dados coletados:")
        print(f"   - Séries econômicas: {len(economic_data)}")
        print(f"   - Asset returns: {asset_returns.shape}")
        print(f"   - Período: {asset_returns.index.min()} a {asset_returns.index.max()}")
        
        # Inicializar gerador de sinais
        print("\n🚀 Inicializando gerador de sinais...")
        signal_generator = ProbabilisticSignalGenerator()
        
        # Gerar sinais
        print("🎯 Gerando sinais probabilísticos...")
        result = signal_generator.generate_signals(
            economic_data=economic_data,
            asset_returns=asset_returns
        )
        
        # Verificar resultado
        if 'error' in result:
            print(f"❌ Erro na geração de sinais: {result['error']}")
            return False
        
        # Analisar resultados
        print("\n📈 ANÁLISE DOS RESULTADOS")
        print("=" * 50)
        
        signals_df = result['signals']
        if not signals_df.empty:
            print(f"✅ Sinais gerados: {len(signals_df)} pontos")
            print(f"   Período: {signals_df.index.min()} a {signals_df.index.max()}")
            
            # Estatísticas dos sinais
            if 'buy_signal' in signals_df.columns:
                buy_signals = signals_df['buy_signal'].sum()
                sell_signals = signals_df['sell_signal'].sum() if 'sell_signal' in signals_df.columns else 0
                hold_signals = signals_df['hold_signal'].sum() if 'hold_signal' in signals_df.columns else 0
                
                print(f"   - Sinais de compra: {buy_signals}")
                print(f"   - Sinais de venda: {sell_signals}")
                print(f"   - Sinais de hold: {hold_signals}")
            
            # Probabilidades
            if 'buy_probability' in signals_df.columns:
                avg_buy_prob = signals_df['buy_probability'].mean()
                avg_sell_prob = signals_df['sell_probability'].mean() if 'sell_probability' in signals_df.columns else 0
                print(f"   - Probabilidade média de compra: {avg_buy_prob:.2%}")
                print(f"   - Probabilidade média de venda: {avg_sell_prob:.2%}")
            
            # Regimes
            if 'most_likely_regime' in signals_df.columns:
                regimes = signals_df['most_likely_regime'].value_counts()
                print(f"   - Distribuição de regimes:")
                for regime, count in regimes.items():
                    print(f"     * Regime {regime}: {count} pontos")
        
        # HRP Allocation
        hrp_allocation = result['hrp_allocation']
        if 'allocation' in hrp_allocation:
            print(f"\n💰 ALOCAÇÃO HRP:")
            for asset, allocation in hrp_allocation['allocation'].items():
                print(f"   - {asset}: {allocation:.2%}")
        
        # Resumo
        summary = result['summary']
        if summary and 'total_signals' in summary:
            print(f"\n📋 RESUMO:")
            print(f"   - Total de sinais: {summary['total_signals']}")
            print(f"   - Taxa de compra: {summary.get('buy_percentage', 0):.1f}%")
            print(f"   - Taxa de venda: {summary.get('sell_percentage', 0):.1f}%")
            print(f"   - Confiança média: {summary.get('avg_confidence', 0):.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de geração de sinais: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_signal_validation():
    """Testa validação dos sinais gerados"""
    print("\n🔍 TESTANDO VALIDAÇÃO DOS SINAIS")
    print("=" * 50)
    
    try:
        # Coletar dados
        economic_data, asset_returns = await collect_real_data()
        
        if not economic_data or asset_returns.empty:
            print("❌ Dados insuficientes para validação")
            return False
        
        # Gerar sinais
        signal_generator = ProbabilisticSignalGenerator()
        result = signal_generator.generate_signals(
            economic_data=economic_data,
            asset_returns=asset_returns
        )
        
        if 'error' in result:
            print(f"❌ Erro na geração: {result['error']}")
            return False
        
        signals_df = result['signals']
        
        # Validações
        validations = []
        
        # 1. Verificar se DataFrame não está vazio
        if signals_df.empty:
            validations.append("❌ DataFrame de sinais vazio")
        else:
            validations.append("✅ DataFrame de sinais não vazio")
        
        # 2. Verificar colunas essenciais
        essential_columns = ['buy_probability', 'sell_probability']
        missing_columns = [col for col in essential_columns if col not in signals_df.columns]
        if missing_columns:
            validations.append(f"❌ Colunas ausentes: {missing_columns}")
        else:
            validations.append("✅ Todas as colunas essenciais presentes")
        
        # 3. Verificar se probabilidades estão entre 0 e 1
        if 'buy_probability' in signals_df.columns:
            buy_prob_valid = (signals_df['buy_probability'] >= 0).all() and (signals_df['buy_probability'] <= 1).all()
            if buy_prob_valid:
                validations.append("✅ Probabilidades de compra válidas (0-1)")
            else:
                validations.append("❌ Probabilidades de compra fora do range (0-1)")
        
        if 'sell_probability' in signals_df.columns:
            sell_prob_valid = (signals_df['sell_probability'] >= 0).all() and (signals_df['sell_probability'] <= 1).all()
            if sell_prob_valid:
                validations.append("✅ Probabilidades de venda válidas (0-1)")
            else:
                validations.append("❌ Probabilidades de venda fora do range (0-1)")
        
        # 4. Verificar se não há valores NaN
        nan_count = signals_df.isnull().sum().sum()
        if nan_count == 0:
            validations.append("✅ Nenhum valor NaN encontrado")
        else:
            validations.append(f"❌ {nan_count} valores NaN encontrados")
        
        # 5. Verificar consistência temporal
        if len(signals_df) > 1:
            time_diff = signals_df.index[1] - signals_df.index[0]
            if time_diff.days >= 20 and time_diff.days <= 35:  # Aproximadamente mensal
                validations.append("✅ Intervalo temporal consistente (mensal)")
            else:
                validations.append(f"⚠️ Intervalo temporal irregular: {time_diff.days} dias")
        
        # Imprimir validações
        for validation in validations:
            print(validation)
        
        # Contar sucessos
        success_count = sum(1 for v in validations if v.startswith("✅"))
        total_count = len(validations)
        
        print(f"\n📊 Resultado da validação: {success_count}/{total_count} testes passaram")
        
        return success_count >= total_count * 0.8  # 80% de sucesso
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False

async def main():
    """Executa todos os testes de geração de sinais"""
    print("🚀 INICIANDO TESTES DE GERAÇÃO DE SINAIS COM DADOS REAIS")
    print("=" * 70)
    
    results = []
    
    # Testar geração de sinais
    results.append(await test_signal_generation())
    
    # Testar validação
    results.append(await test_signal_validation())
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES DE GERAÇÃO DE SINAIS PASSARAM!")
        return True
    else:
        print(f"\n⚠️ {total - passed} TESTE(S) FALHARAM!")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
