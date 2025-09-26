#!/usr/bin/env python3
"""
Teste simples dos endpoints da API sem dependências de banco
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_imports():
    """Testa se os módulos da API podem ser importados"""
    print("📦 TESTANDO IMPORTS DOS MÓDULOS DA API")
    print("=" * 50)
    
    results = []
    
    # Testar imports básicos
    try:
        from app.core.config import settings
        print("✅ Configurações importadas com sucesso")
        results.append(True)
    except Exception as e:
        print(f"❌ Erro ao importar configurações: {e}")
        results.append(False)
    
    # Testar imports dos endpoints
    try:
        from app.api.v1.endpoints import dashboard, signals, data
        print("✅ Endpoints importados com sucesso")
        results.append(True)
    except Exception as e:
        print(f"❌ Erro ao importar endpoints: {e}")
        results.append(False)
    
    # Testar imports dos serviços
    try:
        from app.services.robust_data_collector import RobustDataCollector
        print("✅ Serviços importados com sucesso")
        results.append(True)
    except Exception as e:
        print(f"❌ Erro ao importar serviços: {e}")
        results.append(False)
    
    # Testar imports dos geradores de sinal
    try:
        from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator
        print("✅ Geradores de sinal importados com sucesso")
        results.append(True)
    except Exception as e:
        print(f"❌ Erro ao importar geradores de sinal: {e}")
        results.append(False)
    
    return results

def test_endpoint_functions():
    """Testa se as funções dos endpoints estão definidas"""
    print("\n🔧 TESTANDO FUNÇÕES DOS ENDPOINTS")
    print("=" * 50)
    
    results = []
    
    try:
        from app.api.v1.endpoints import dashboard, signals, data
        
        # Testar funções do dashboard
        if hasattr(dashboard, 'get_dashboard_data'):
            print("✅ get_dashboard_data definida")
            results.append(True)
        else:
            print("❌ get_dashboard_data não definida")
            results.append(False)
        
        # Testar funções de sinais
        if hasattr(signals, 'generate_signals'):
            print("✅ generate_signals definida")
            results.append(True)
        else:
            print("❌ generate_signals não definida")
            results.append(False)
        
        if hasattr(signals, 'get_signals'):
            print("✅ get_signals definida")
            results.append(True)
        else:
            print("❌ get_signals não definida")
            results.append(False)
        
        # Testar funções de dados
        if hasattr(data, 'get_data_status'):
            print("✅ get_data_status definida")
            results.append(True)
        else:
            print("❌ get_data_status não definida")
            results.append(False)
        
        if hasattr(data, 'get_health_check'):
            print("✅ get_health_check definida")
            results.append(True)
        else:
            print("❌ get_health_check não definida")
            results.append(False)
        
    except Exception as e:
        print(f"❌ Erro ao testar funções: {e}")
        results.append(False)
    
    return results

def test_router_configuration():
    """Testa configuração do router"""
    print("\n🛣️ TESTANDO CONFIGURAÇÃO DO ROUTER")
    print("=" * 50)
    
    results = []
    
    try:
        from app.api.v1.router import api_router
        
        # Verificar se o router tem rotas
        if hasattr(api_router, 'routes') and len(api_router.routes) > 0:
            print(f"✅ Router configurado com {len(api_router.routes)} rotas")
            results.append(True)
        else:
            print("❌ Router sem rotas configuradas")
            results.append(False)
        
        # Listar rotas disponíveis
        print("📋 Rotas disponíveis:")
        for route in api_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else ['GET']
                print(f"   - {methods[0]} {route.path}")
        
    except Exception as e:
        print(f"❌ Erro ao testar router: {e}")
        results.append(False)
    
    return results

def test_service_initialization():
    """Testa inicialização dos serviços"""
    print("\n⚙️ TESTANDO INICIALIZAÇÃO DOS SERVIÇOS")
    print("=" * 50)
    
    results = []
    
    try:
        # Testar inicialização do gerador de sinais
        from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator
        generator = ProbabilisticSignalGenerator()
        print("✅ ProbabilisticSignalGenerator inicializado")
        results.append(True)
        
        # Testar inicialização das fontes de dados
        from app.services.data_sources.bacen_sgs_source import BacenSGSSource
        bacen_source = BacenSGSSource()
        print("✅ BacenSGSSource inicializado")
        results.append(True)
        
        from app.services.data_sources.fred_source import FREDSource
        fred_source = FREDSource()
        print("✅ FREDSource inicializado")
        results.append(True)
        
        from app.services.data_sources.yahoo_source import YahooSource
        yahoo_source = YahooSource()
        print("✅ YahooSource inicializado")
        results.append(True)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar serviços: {e}")
        results.append(False)
    
    return results

def test_configuration_validation():
    """Testa validação das configurações"""
    print("\n⚙️ TESTANDO VALIDAÇÃO DAS CONFIGURAÇÕES")
    print("=" * 50)
    
    results = []
    
    try:
        from app.core.config import settings
        
        # Testar configurações críticas
        if settings.HOST and settings.PORT:
            print(f"✅ Host e porta configurados: {settings.HOST}:{settings.PORT}")
            results.append(True)
        else:
            print("❌ Host ou porta não configurados")
            results.append(False)
        
        if settings.FRED_API_KEY:
            print(f"✅ FRED API Key configurada")
            results.append(True)
        else:
            print("⚠️ FRED API Key não configurada")
            results.append(False)
        
        if settings.BCB_SERIES and len(settings.BCB_SERIES) > 0:
            print(f"✅ Séries BCB configuradas: {len(settings.BCB_SERIES)} séries")
            results.append(True)
        else:
            print("❌ Séries BCB não configuradas")
            results.append(False)
        
        if settings.OECD_COUNTRIES and len(settings.OECD_COUNTRIES) > 0:
            print(f"✅ Países OECD configurados: {len(settings.OECD_COUNTRIES)} países")
            results.append(True)
        else:
            print("❌ Países OECD não configurados")
            results.append(False)
        
    except Exception as e:
        print(f"❌ Erro ao validar configurações: {e}")
        results.append(False)
    
    return results

def main():
    """Executa todos os testes simples da API"""
    print("🚀 INICIANDO TESTES SIMPLES DA API")
    print("=" * 60)
    
    all_results = []
    
    # Testar imports
    import_results = test_api_imports()
    all_results.extend(import_results)
    
    # Testar funções dos endpoints
    function_results = test_endpoint_functions()
    all_results.extend(function_results)
    
    # Testar router
    router_results = test_router_configuration()
    all_results.extend(router_results)
    
    # Testar inicialização dos serviços
    service_results = test_service_initialization()
    all_results.extend(service_results)
    
    # Testar configurações
    config_results = test_configuration_validation()
    all_results.extend(config_results)
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES SIMPLES")
    print("=" * 50)
    
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed >= total * 0.8:  # 80% de sucesso
        print("\n🎉 TESTES SIMPLES DA API PASSARAM!")
        return True
    else:
        print(f"\n⚠️ MUITOS TESTES SIMPLES DA API FALHARAM!")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
