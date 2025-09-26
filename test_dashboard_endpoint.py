#!/usr/bin/env python3
"""
Teste do endpoint do dashboard com dados reais
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.v1.endpoints.dashboard import get_dashboard_data
from app.core.database import SessionLocal
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dashboard_endpoint():
    """Testa o endpoint do dashboard com dados reais"""
    print("🌐 TESTANDO ENDPOINT DO DASHBOARD COM DADOS REAIS")
    print("=" * 60)
    
    try:
        # Simular sessão de banco
        db = SessionLocal()
        
        # Chamar o endpoint
        print("📊 Chamando endpoint get_dashboard_data...")
        result = await get_dashboard_data(db)
        
        print(f"✅ Endpoint executado com sucesso!")
        print(f"📊 Tipo do resultado: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📋 Chaves do resultado: {list(result.keys())}")
            
            # Verificar estrutura dos dados
            if 'currentSignal' in result:
                print(f"✅ Sinal atual presente")
                current_signal = result['currentSignal']
                print(f"   - Data: {current_signal.get('date', 'N/A')}")
                print(f"   - Sinal: {current_signal.get('signal', 'N/A')}")
                print(f"   - Confiança: {current_signal.get('confidence', 0)}%")
                print(f"   - Regime: {current_signal.get('regime', 'N/A')}")
            
            if 'cliData' in result:
                cli_data = result['cliData']
                print(f"✅ Dados CLI: {len(cli_data)} pontos")
                if cli_data:
                    print(f"   - Primeiro ponto: {cli_data[0]}")
                    print(f"   - Último ponto: {cli_data[-1]}")
            
            if 'performance' in result:
                performance = result['performance']
                print(f"✅ Métricas de performance:")
                print(f"   - Total de sinais: {performance.get('totalSignals', 0)}")
                print(f"   - Sinais de compra: {performance.get('buySignals', 0)}")
                print(f"   - Sinais de venda: {performance.get('sellSignals', 0)}")
                print(f"   - Sinais de hold: {performance.get('holdSignals', 0)}")
                print(f"   - Confiança média: {performance.get('avgConfidence', 0)}%")
            
            if 'assets' in result:
                assets = result['assets']
                print(f"✅ Ativos: {len(assets)}")
                for asset in assets:
                    print(f"   - {asset.get('ticker', 'N/A')}: {asset.get('allocation', 0)}%")
            
            if 'lastUpdate' in result:
                print(f"✅ Última atualização: {result['lastUpdate']}")
        
        # Salvar resultado em arquivo para análise
        with open('dashboard_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Resultado salvo em: dashboard_test_result.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Executa o teste do endpoint"""
    print("🚀 INICIANDO TESTE DO ENDPOINT DO DASHBOARD")
    print("=" * 60)
    
    success = await test_dashboard_endpoint()
    
    if success:
        print("\n🎉 TESTE DO ENDPOINT PASSOU!")
        print("✅ Dashboard backend está funcionando com dados reais")
        return True
    else:
        print("\n❌ TESTE DO ENDPOINT FALHOU!")
        print("⚠️ Verificar configuração do backend")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
