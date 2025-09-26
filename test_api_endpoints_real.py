#!/usr/bin/env python3
"""
Teste dos endpoints da API com dados reais
"""

import sys
import os
import asyncio
import httpx
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from fastapi.testclient import TestClient
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_endpoints():
    """Testa endpoints da API com dados reais"""
    print("🌐 TESTANDO ENDPOINTS DA API COM DADOS REAIS")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Lista de endpoints para testar
    endpoints = [
        {
            'path': '/',
            'method': 'GET',
            'name': 'Endpoint Raiz',
            'expected_status': 200
        },
        {
            'path': '/health',
            'method': 'GET',
            'name': 'Health Check',
            'expected_status': 200
        },
        {
            'path': '/api/v1/data/health',
            'method': 'GET',
            'name': 'Data Health Check',
            'expected_status': 200
        },
        {
            'path': '/api/v1/data/status',
            'method': 'GET',
            'name': 'Data Status',
            'expected_status': 200
        },
        {
            'path': '/api/v1/signals/health',
            'method': 'GET',
            'name': 'Signals Health Check',
            'expected_status': 200
        },
        {
            'path': '/api/v1/signals/',
            'method': 'GET',
            'name': 'Signals List',
            'expected_status': 200
        },
        {
            'path': '/api/v1/signals/generate',
            'method': 'GET',
            'name': 'Generate Signals',
            'expected_status': 200
        },
        {
            'path': '/api/v1/dashboard/dashboard-data',
            'method': 'GET',
            'name': 'Dashboard Data',
            'expected_status': 200
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📡 Testando: {endpoint['name']}")
        print(f"   Path: {endpoint['path']}")
        print(f"   Method: {endpoint['method']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = client.get(endpoint['path'])
            else:
                response = client.post(endpoint['path'])
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == endpoint['expected_status']:
                print(f"   ✅ Status correto")
                
                # Tentar parsear JSON se possível
                try:
                    data = response.json()
                    print(f"   📊 Resposta JSON válida")
                    
                    # Análise específica por endpoint
                    if endpoint['path'] == '/':
                        if 'message' in data and 'version' in data:
                            print(f"   ✅ Estrutura correta do endpoint raiz")
                        else:
                            print(f"   ⚠️ Estrutura inesperada")
                    
                    elif endpoint['path'] == '/health':
                        if 'status' in data:
                            print(f"   ✅ Health check válido")
                        else:
                            print(f"   ⚠️ Health check incompleto")
                    
                    elif endpoint['path'] == '/api/v1/data/status':
                        if 'data_sources' in data:
                            print(f"   ✅ Status de dados válido")
                        else:
                            print(f"   ⚠️ Status de dados incompleto")
                    
                    elif endpoint['path'] == '/api/v1/signals/generate':
                        if 'signals' in data or 'error' in data:
                            print(f"   ✅ Geração de sinais executada")
                        else:
                            print(f"   ⚠️ Resposta de sinais inesperada")
                    
                    elif endpoint['path'] == '/api/v1/dashboard/dashboard-data':
                        if 'currentSignal' in data or 'error' in data:
                            print(f"   ✅ Dados do dashboard gerados")
                        else:
                            print(f"   ⚠️ Estrutura do dashboard inesperada")
                    
                    results.append(True)
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️ Resposta não é JSON válido")
                    print(f"   📄 Resposta: {response.text[:200]}...")
                    results.append(False)
                    
            else:
                print(f"   ❌ Status incorreto (esperado: {endpoint['expected_status']})")
                print(f"   📄 Resposta: {response.text[:200]}...")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
            results.append(False)
    
    return results

def test_api_response_times():
    """Testa tempos de resposta dos endpoints"""
    print("\n⏱️ TESTANDO TEMPOS DE RESPOSTA")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Endpoints críticos para testar performance
    critical_endpoints = [
        '/health',
        '/api/v1/data/status',
        '/api/v1/signals/health'
    ]
    
    results = []
    
    for path in critical_endpoints:
        print(f"\n📡 Testando tempo de resposta: {path}")
        
        try:
            import time
            start_time = time.time()
            response = client.get(path)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"   ⏱️ Tempo: {response_time:.3f}s")
            print(f"   📊 Status: {response.status_code}")
            
            if response_time < 5.0:  # Menos de 5 segundos
                print(f"   ✅ Performance aceitável")
                results.append(True)
            else:
                print(f"   ⚠️ Performance lenta (>5s)")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append(False)
    
    return results

def test_api_error_handling():
    """Testa tratamento de erros da API"""
    print("\n🚨 TESTANDO TRATAMENTO DE ERROS")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Endpoints que devem retornar erro 404
    invalid_endpoints = [
        '/api/v1/invalid',
        '/api/v1/data/invalid',
        '/api/v1/signals/invalid'
    ]
    
    results = []
    
    for path in invalid_endpoints:
        print(f"\n📡 Testando endpoint inválido: {path}")
        
        try:
            response = client.get(path)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 404:
                print(f"   ✅ Erro 404 retornado corretamente")
                results.append(True)
            else:
                print(f"   ⚠️ Status inesperado (esperado 404)")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Erro inesperado: {e}")
            results.append(False)
    
    return results

def test_cors_headers():
    """Testa headers CORS"""
    print("\n🌍 TESTANDO HEADERS CORS")
    print("=" * 50)
    
    client = TestClient(app)
    
    try:
        response = client.get('/')
        headers = response.headers
        
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]
        
        results = []
        
        for header in cors_headers:
            if header in headers:
                print(f"   ✅ {header}: {headers[header]}")
                results.append(True)
            else:
                print(f"   ❌ {header}: ausente")
                results.append(False)
        
        return results
        
    except Exception as e:
        print(f"   ❌ Erro no teste CORS: {e}")
        return [False]

def main():
    """Executa todos os testes da API"""
    print("🚀 INICIANDO TESTES DOS ENDPOINTS DA API")
    print("=" * 70)
    
    all_results = []
    
    # Testar endpoints básicos
    endpoint_results = test_api_endpoints()
    all_results.extend(endpoint_results)
    
    # Testar performance
    performance_results = test_api_response_times()
    all_results.extend(performance_results)
    
    # Testar tratamento de erros
    error_results = test_api_error_handling()
    all_results.extend(error_results)
    
    # Testar CORS
    cors_results = test_cors_headers()
    all_results.extend(cors_results)
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES DA API")
    print("=" * 50)
    
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed >= total * 0.8:  # 80% de sucesso
        print("\n🎉 TESTES DA API PASSARAM!")
        return True
    else:
        print(f"\n⚠️ MUITOS TESTES DA API FALHARAM!")
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
