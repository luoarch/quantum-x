#!/usr/bin/env python3
"""
Teste do módulo de configuração com dados reais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config_loading():
    """Testa carregamento das configurações"""
    print("🔧 TESTANDO CONFIGURAÇÕES")
    print("=" * 50)
    
    # Testar configurações básicas
    print(f"✅ Host: {settings.HOST}")
    print(f"✅ Port: {settings.PORT}")
    print(f"✅ Debug: {settings.DEBUG}")
    print(f"✅ Log Level: {settings.LOG_LEVEL}")
    
    # Testar configurações de banco
    print(f"✅ Database URL: {settings.DATABASE_URL}")
    print(f"✅ Redis URL: {settings.REDIS_URL}")
    
    # Testar API Keys
    print(f"✅ FRED API Key: {settings.FRED_API_KEY[:10]}..." if settings.FRED_API_KEY else "❌ FRED API Key não configurada")
    print(f"✅ BCB API Key: {'Configurada' if settings.BCB_API_KEY else 'Não configurada'}")
    print(f"✅ OECD API Key: {'Configurada' if settings.OECD_API_KEY else 'Não configurada'}")
    print(f"✅ Trading Economics API Key: {'Configurada' if settings.TRADING_ECONOMICS_API_KEY else 'Não configurada'}")
    
    # Testar configurações de rate limiting
    print(f"✅ OECD Rate Limit: {settings.OECD_RATE_LIMIT}s")
    print(f"✅ BCB Rate Limit: {settings.BCB_RATE_LIMIT}s")
    print(f"✅ IPEA Rate Limit: {settings.IPEA_RATE_LIMIT}s")
    
    # Testar séries configuradas
    print(f"✅ BCB Series: {settings.BCB_SERIES}")
    print(f"✅ IPEA Series: {settings.IPEA_SERIES}")
    print(f"✅ OECD Countries: {settings.OECD_COUNTRIES}")
    
    # Testar URLs base
    print(f"✅ BCB Base URL: {settings.BCB_BASE_URL}")
    print(f"✅ IPEA Base URL: {settings.IPEA_BASE_URL}")
    print(f"✅ OECD Base URL: {settings.OECD_BASE_URL}")
    print(f"✅ Trading Economics Base URL: {settings.TRADING_ECONOMICS_BASE_URL}")
    
    print("\n✅ CONFIGURAÇÕES CARREGADAS COM SUCESSO!")

def test_config_validation():
    """Testa validação das configurações"""
    print("\n🔍 VALIDANDO CONFIGURAÇÕES")
    print("=" * 50)
    
    errors = []
    
    # Validar URLs
    if not settings.BCB_BASE_URL.startswith('http'):
        errors.append("BCB Base URL inválida")
    
    if not settings.IPEA_BASE_URL.startswith('http'):
        errors.append("IPEA Base URL inválida")
    
    if not settings.OECD_BASE_URL.startswith('http'):
        errors.append("OECD Base URL inválida")
    
    # Validar portas e hosts
    if not isinstance(settings.PORT, int) or settings.PORT < 1 or settings.PORT > 65535:
        errors.append("Porta inválida")
    
    if not settings.HOST:
        errors.append("Host não configurado")
    
    # Validar rate limits
    if settings.OECD_RATE_LIMIT <= 0:
        errors.append("OECD Rate Limit inválido")
    
    if settings.BCB_RATE_LIMIT <= 0:
        errors.append("BCB Rate Limit inválido")
    
    # Validar séries
    if not isinstance(settings.BCB_SERIES, dict) or not settings.BCB_SERIES:
        errors.append("BCB Series não configuradas")
    
    if not isinstance(settings.OECD_COUNTRIES, list) or not settings.OECD_COUNTRIES:
        errors.append("OECD Countries não configurados")
    
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ TODAS AS CONFIGURAÇÕES SÃO VÁLIDAS!")
        return True

if __name__ == "__main__":
    try:
        test_config_loading()
        success = test_config_validation()
        
        if success:
            print("\n🎉 TESTE DE CONFIGURAÇÃO PASSOU!")
            sys.exit(0)
        else:
            print("\n❌ TESTE DE CONFIGURAÇÃO FALHOU!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE DE CONFIGURAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
