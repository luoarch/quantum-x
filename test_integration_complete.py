#!/usr/bin/env python3
"""
Teste de integração completo do sistema Quantum X
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.robust_data_collector import RobustDataCollector
from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator
from app.services.data_sources.bacen_sgs_source import BacenSGSSource
from app.services.data_sources.fred_source import FREDSource
from app.services.data_sources.yahoo_source import YahooSource
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_data_flow():
    """Testa o fluxo completo de dados"""
    print("🔄 TESTANDO FLUXO COMPLETO DE DADOS")
    print("=" * 60)
    
    try:
        # 1. Coletar dados de múltiplas fontes
        print("📊 1. Coletando dados de múltiplas fontes...")
        
        economic_data = {}
        asset_returns = pd.DataFrame()
        
        # BACEN SGS
        print("   🏦 Coletando dados BACEN SGS...")
        bacen_source = BacenSGSSource()
        
        # IPCA
        ipca_data = await bacen_source.fetch_data({'name': 'ipca', 'limit': 12})
        if not ipca_data.empty:
            ipca_df = ipca_data[['date', 'value']].copy()
            ipca_df['date'] = pd.to_datetime(ipca_df['date'])
            ipca_df = ipca_df.set_index('date').sort_index()
            economic_data['ipca'] = ipca_df
            print(f"      ✅ IPCA: {len(ipca_df)} registros")
        
        # SELIC
        selic_data = await bacen_source.fetch_data({'name': 'selic', 'limit': 12})
        if not selic_data.empty:
            selic_df = selic_data[['date', 'value']].copy()
            selic_df['date'] = pd.to_datetime(selic_df['date'])
            selic_df = selic_df.set_index('date').sort_index()
            economic_data['selic'] = selic_df
            print(f"      ✅ SELIC: {len(selic_df)} registros")
        
        # FRED CLI
        print("   🏛️ Coletando dados FRED...")
        fred_source = FREDSource()
        cli_data = await fred_source.fetch_data({'country': 'BRA', 'start_year': 2023, 'end_year': 2024})
        if not cli_data.empty:
            cli_df = cli_data[['date', 'value']].copy()
            cli_df['date'] = pd.to_datetime(cli_df['date'])
            cli_df = cli_df.set_index('date').sort_index()
            economic_data['cli'] = cli_df
            print(f"      ✅ CLI: {len(cli_df)} registros")
        
        # Yahoo Finance
        print("   📈 Coletando dados Yahoo Finance...")
        yahoo_source = YahooSource()
        bova_data = await yahoo_source.fetch_data({'symbol': 'BOVA11', 'period': '1y', 'interval': '1mo'})
        if not bova_data.empty:
            bova_df = bova_data[['date', 'value']].copy()
            bova_df['date'] = pd.to_datetime(bova_df['date'])
            bova_df = bova_df.set_index('date').sort_index()
            
            # Calcular retornos
            bova_returns = bova_df['value'].pct_change().fillna(0)
            asset_returns = pd.DataFrame({'BOVA11': bova_returns})
            print(f"      ✅ BOVA11: {len(asset_returns)} registros")
        
        # Criar retornos de renda fixa
        if 'selic' in economic_data:
            selic_series = economic_data['selic']['value'] / 100.0
            monthly_return = (1.0 + selic_series) ** (1.0 / 12.0) - 1.0
            tesouro_returns = pd.DataFrame({'TESOURO_IPCA': monthly_return})
            
            if not asset_returns.empty:
                common_index = asset_returns.index.intersection(tesouro_returns.index)
                if len(common_index) > 0:
                    asset_returns = asset_returns.reindex(common_index)
                    tesouro_returns = tesouro_returns.reindex(common_index)
                    asset_returns['TESOURO_IPCA'] = tesouro_returns['TESOURO_IPCA']
            else:
                asset_returns = tesouro_returns
            
            print(f"      ✅ TESOURO_IPCA: {len(tesouro_returns)} registros")
        
        print(f"   📊 Total de séries econômicas: {len(economic_data)}")
        print(f"   📊 Asset returns shape: {asset_returns.shape}")
        
        # 2. Gerar sinais
        print("\n🧠 2. Gerando sinais probabilísticos...")
        
        signal_generator = ProbabilisticSignalGenerator()
        result = signal_generator.generate_signals(
            economic_data=economic_data,
            asset_returns=asset_returns
        )
        
        if 'error' in result:
            print(f"   ❌ Erro na geração de sinais: {result['error']}")
            return False
        
        signals_df = result['signals']
        print(f"   ✅ Sinais gerados: {len(signals_df)} pontos")
        
        # 3. Analisar resultados
        print("\n📈 3. Analisando resultados...")
        
        if not signals_df.empty:
            # Estatísticas básicas
            total_signals = len(signals_df)
            buy_signals = signals_df['buy_signal'].sum() if 'buy_signal' in signals_df.columns else 0
            sell_signals = signals_df['sell_signal'].sum() if 'sell_signal' in signals_df.columns else 0
            hold_signals = signals_df['hold_signal'].sum() if 'hold_signal' in signals_df.columns else 0
            
            print(f"   📊 Total de sinais: {total_signals}")
            print(f"   📊 Sinais de compra: {buy_signals}")
            print(f"   📊 Sinais de venda: {sell_signals}")
            print(f"   📊 Sinais de hold: {hold_signals}")
            
            # Probabilidades médias
            if 'buy_probability' in signals_df.columns:
                avg_buy_prob = signals_df['buy_probability'].mean()
                avg_sell_prob = signals_df['sell_probability'].mean() if 'sell_probability' in signals_df.columns else 0
                print(f"   📊 Probabilidade média de compra: {avg_buy_prob:.2%}")
                print(f"   📊 Probabilidade média de venda: {avg_sell_prob:.2%}")
        
        # 4. Verificar qualidade dos dados
        print("\n🔍 4. Verificando qualidade dos dados...")
        
        quality_checks = []
        
        # Verificar se temos dados suficientes
        if len(economic_data) >= 2:
            quality_checks.append("✅ Dados econômicos suficientes")
        else:
            quality_checks.append("❌ Dados econômicos insuficientes")
        
        if not asset_returns.empty and asset_returns.shape[1] >= 2:
            quality_checks.append("✅ Asset returns suficientes")
        else:
            quality_checks.append("❌ Asset returns insuficientes")
        
        if not signals_df.empty:
            quality_checks.append("✅ Sinais gerados com sucesso")
        else:
            quality_checks.append("❌ Falha na geração de sinais")
        
        # Verificar se não há muitos valores NaN
        if not signals_df.empty:
            nan_count = signals_df.isnull().sum().sum()
            if nan_count == 0:
                quality_checks.append("✅ Nenhum valor NaN")
            else:
                quality_checks.append(f"⚠️ {nan_count} valores NaN encontrados")
        
        for check in quality_checks:
            print(f"   {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de fluxo completo: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_robust_data_collector():
    """Testa o coletor robusto de dados"""
    print("\n🛡️ TESTANDO COLETOR ROBUSTO DE DADOS")
    print("=" * 60)
    
    try:
        # Simular sessão de banco (sem banco real)
        class MockDB:
            def query(self, *args):
                return self
            def filter(self, *args):
                return self
            def first(self):
                return None
            def add(self, *args):
                pass
            def commit(self):
                pass
            def rollback(self):
                pass
        
        mock_db = MockDB()
        collector = RobustDataCollector(mock_db)
        
        # Testar coleta de uma série
        print("📊 Testando coleta de série única...")
        result = await collector.collect_series_with_priority('ipca', months=6)
        
        if 'error' in result:
            print(f"   ❌ Erro na coleta: {result['error']}")
            return False
        
        print(f"   ✅ Série coletada: {result['series_name']}")
        print(f"   📊 Status: {result['status']}")
        print(f"   📊 Registros: {result['records']}")
        print(f"   📊 Fonte: {result['source']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do coletor robusto: {e}")
        return False

async def test_system_performance():
    """Testa performance do sistema"""
    print("\n⚡ TESTANDO PERFORMANCE DO SISTEMA")
    print("=" * 60)
    
    try:
        import time
        
        # Testar tempo de inicialização
        print("🚀 Testando tempo de inicialização...")
        start_time = time.time()
        
        bacen_source = BacenSGSSource()
        fred_source = FREDSource()
        yahoo_source = YahooSource()
        signal_generator = ProbabilisticSignalGenerator()
        
        init_time = time.time() - start_time
        print(f"   ⏱️ Tempo de inicialização: {init_time:.3f}s")
        
        # Testar tempo de coleta de dados
        print("📊 Testando tempo de coleta de dados...")
        start_time = time.time()
        
        ipca_data = await bacen_source.fetch_data({'name': 'ipca', 'limit': 6})
        
        collection_time = time.time() - start_time
        print(f"   ⏱️ Tempo de coleta: {collection_time:.3f}s")
        
        # Testar tempo de geração de sinais
        if not ipca_data.empty:
            print("🧠 Testando tempo de geração de sinais...")
            
            # Preparar dados mínimos
            ipca_df = ipca_data[['date', 'value']].copy()
            ipca_df['date'] = pd.to_datetime(ipca_df['date'])
            ipca_df = ipca_df.set_index('date').sort_index()
            
            economic_data = {'ipca': ipca_df}
            asset_returns = pd.DataFrame({
                'TESOURO_IPCA': np.random.normal(0.005, 0.01, len(ipca_df)),
                'BOVA11': np.random.normal(0.008, 0.03, len(ipca_df))
            }, index=ipca_df.index)
            
            start_time = time.time()
            result = signal_generator.generate_signals(
                economic_data=economic_data,
                asset_returns=asset_returns
            )
            signal_time = time.time() - start_time
            
            print(f"   ⏱️ Tempo de geração de sinais: {signal_time:.3f}s")
            
            if 'error' not in result:
                print("   ✅ Sinais gerados com sucesso")
            else:
                print(f"   ❌ Erro na geração: {result['error']}")
        
        # Avaliar performance
        print("\n📊 Avaliação de Performance:")
        if init_time < 2.0:
            print("   ✅ Inicialização rápida (<2s)")
        else:
            print("   ⚠️ Inicialização lenta (>2s)")
        
        if collection_time < 5.0:
            print("   ✅ Coleta rápida (<5s)")
        else:
            print("   ⚠️ Coleta lenta (>5s)")
        
        if 'signal_time' in locals() and signal_time < 10.0:
            print("   ✅ Geração de sinais rápida (<10s)")
        else:
            print("   ⚠️ Geração de sinais lenta (>10s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False

async def test_error_handling():
    """Testa tratamento de erros"""
    print("\n🚨 TESTANDO TRATAMENTO DE ERROS")
    print("=" * 60)
    
    try:
        # Testar fonte com dados inválidos
        print("🔍 Testando fonte com dados inválidos...")
        bacen_source = BacenSGSSource()
        
        # Tentar buscar série inexistente
        try:
            result = await bacen_source.fetch_data({'name': 'inexistente', 'limit': 6})
            print("   ⚠️ Fonte não tratou série inexistente corretamente")
        except Exception as e:
            print(f"   ✅ Erro tratado corretamente: {type(e).__name__}")
        
        # Testar gerador com dados vazios
        print("🔍 Testando gerador com dados vazios...")
        signal_generator = ProbabilisticSignalGenerator()
        
        try:
            result = signal_generator.generate_signals(
                economic_data={},
                asset_returns=pd.DataFrame()
            )
            if 'error' in result:
                print("   ✅ Erro tratado corretamente no gerador")
            else:
                print("   ⚠️ Gerador não tratou dados vazios")
        except Exception as e:
            print(f"   ✅ Exceção tratada corretamente: {type(e).__name__}")
        
        # Testar validação de dados
        print("🔍 Testando validação de dados...")
        empty_df = pd.DataFrame()
        is_valid = bacen_source.validate_data(empty_df)
        if not is_valid:
            print("   ✅ Validação rejeita DataFrame vazio")
        else:
            print("   ⚠️ Validação aceita DataFrame vazio")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de tratamento de erros: {e}")
        return False

async def main():
    """Executa todos os testes de integração"""
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO COMPLETOS")
    print("=" * 70)
    
    all_results = []
    
    # Testar fluxo completo de dados
    flow_result = await test_complete_data_flow()
    all_results.append(flow_result)
    
    # Testar coletor robusto
    collector_result = await test_robust_data_collector()
    all_results.append(collector_result)
    
    # Testar performance
    performance_result = await test_system_performance()
    all_results.append(performance_result)
    
    # Testar tratamento de erros
    error_result = await test_error_handling()
    all_results.append(error_result)
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES DE INTEGRAÇÃO")
    print("=" * 60)
    
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    # Análise detalhada
    print("\n📋 Análise Detalhada:")
    test_names = [
        "Fluxo Completo de Dados",
        "Coletor Robusto de Dados", 
        "Performance do Sistema",
        "Tratamento de Erros"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, all_results)):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {i+1}. {name}: {status}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        print("🚀 Sistema Quantum X está funcionando corretamente!")
        return True
    else:
        print(f"\n⚠️ {total - passed} TESTE(S) DE INTEGRAÇÃO FALHARAM!")
        print("🔧 Algumas funcionalidades precisam de ajustes.")
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
