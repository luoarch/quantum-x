#!/usr/bin/env python3
"""
Teste das fontes de dados com APIs reais
"""

import sys
import os
import asyncio
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sources.bacen_sgs_source import BacenSGSSource
from app.services.data_sources.fred_source import FREDSource
from app.services.data_sources.yahoo_source import YahooSource
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bacen_sgs_source():
    """Testa fonte BACEN SGS com dados reais"""
    print("🏦 TESTANDO BACEN SGS SOURCE")
    print("=" * 50)
    
    try:
        source = BacenSGSSource()
        
        # Testar série IPCA
        print("📊 Testando IPCA...")
        ipca_data = await source.fetch_data({
            'name': 'ipca',
            'limit': 12
        })
        
        if not ipca_data.empty:
            print(f"✅ IPCA: {len(ipca_data)} registros")
            print(f"   Período: {ipca_data['date'].min()} a {ipca_data['date'].max()}")
            print(f"   Valor mais recente: {ipca_data['value'].iloc[-1]:.2f}%")
            print(f"   Fonte: {ipca_data['source'].iloc[0]}")
        else:
            print("❌ IPCA: Nenhum dado retornado")
        
        # Testar série SELIC
        print("\n📊 Testando SELIC...")
        selic_data = await source.fetch_data({
            'name': 'selic',
            'limit': 12
        })
        
        if not selic_data.empty:
            print(f"✅ SELIC: {len(selic_data)} registros")
            print(f"   Período: {selic_data['date'].min()} a {selic_data['date'].max()}")
            print(f"   Valor mais recente: {selic_data['value'].iloc[-1]:.2f}%")
        else:
            print("❌ SELIC: Nenhum dado retornado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste BACEN SGS: {e}")
        return False

async def test_fred_source():
    """Testa fonte FRED com dados reais"""
    print("\n🏛️ TESTANDO FRED SOURCE")
    print("=" * 50)
    
    try:
        source = FREDSource()
        
        # Testar CLI OECD
        print("📊 Testando CLI OECD...")
        cli_data = await source.fetch_data({
            'country': 'BRA',
            'start_year': 2023,
            'end_year': 2024
        })
        
        if not cli_data.empty:
            print(f"✅ CLI: {len(cli_data)} registros")
            print(f"   Período: {cli_data['date'].min()} a {cli_data['date'].max()}")
            print(f"   Valor mais recente: {cli_data['value'].iloc[-1]:.2f}")
            print(f"   Fonte: {cli_data['source'].iloc[0]}")
        else:
            print("❌ CLI: Nenhum dado retornado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste FRED: {e}")
        return False

async def test_yahoo_source():
    """Testa fonte Yahoo Finance com dados reais"""
    print("\n📈 TESTANDO YAHOO FINANCE SOURCE")
    print("=" * 50)
    
    try:
        source = YahooSource()
        
        # Testar BOVA11
        print("📊 Testando BOVA11...")
        bova_data = await source.fetch_data({
            'symbol': 'BOVA11',
            'period': '1y',
            'interval': '1mo'
        })
        
        if not bova_data.empty:
            print(f"✅ BOVA11: {len(bova_data)} registros")
            print(f"   Período: {bova_data['date'].min()} a {bova_data['date'].max()}")
            print(f"   Preço mais recente: R$ {bova_data['value'].iloc[-1]:.2f}")
            print(f"   Fonte: {bova_data['source'].iloc[0]}")
        else:
            print("❌ BOVA11: Nenhum dado retornado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste Yahoo Finance: {e}")
        return False

async def test_data_validation():
    """Testa validação dos dados coletados"""
    print("\n🔍 TESTANDO VALIDAÇÃO DE DADOS")
    print("=" * 50)
    
    try:
        # Testar BACEN SGS
        source = BacenSGSSource()
        ipca_data = await source.fetch_data({'name': 'ipca', 'limit': 6})
        
        is_valid = source.validate_data(ipca_data)
        print(f"✅ Validação BACEN SGS: {'PASSOU' if is_valid else 'FALHOU'}")
        
        if not is_valid:
            print("   Motivos possíveis:")
            print("   - DataFrame vazio")
            print("   - Colunas ausentes (date, value, source)")
            print("   - Valores não monotônicos")
            print("   - Muitos valores nulos (>10%)")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False

async def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE FONTES DE DADOS REAIS")
    print("=" * 60)
    
    results = []
    
    # Testar BACEN SGS
    results.append(await test_bacen_sgs_source())
    
    # Testar FRED
    results.append(await test_fred_source())
    
    # Testar Yahoo Finance
    results.append(await test_yahoo_source())
    
    # Testar validação
    results.append(await test_data_validation())
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES DE FONTES DE DADOS PASSARAM!")
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
