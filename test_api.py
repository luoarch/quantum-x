#!/usr/bin/env python3
"""
Script para testar a API FED-Selic
"""

import requests
import json
import time
from datetime import datetime

# Configuração
API_BASE_URL = "http://localhost:8000"
API_KEY = "dev-key-123"  # Chave de desenvolvimento

def test_api():
    """Testar a API"""
    print("🚀 TESTANDO API FED-SELIC")
    print("=" * 50)
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 1. Testar health check
    print("\n1. 🏥 TESTANDO HEALTH CHECK")
    try:
        response = requests.get(f"{API_BASE_URL}/health/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status da API: {health_data['status']}")
            print(f"   Versão: {health_data['version']}")
            print(f"   Modelo: {health_data['model_version']}")
            print(f"   Uptime: {health_data['uptime_seconds']:.1f}s")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 2. Testar informações da API
    print("\n2. 📋 TESTANDO INFORMAÇÕES DA API")
    try:
        response = requests.get(f"{API_BASE_URL}/info", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            info_data = response.json()
            print(f"   Nome: {info_data['api']['name']}")
            print(f"   Endpoints: {len(info_data['endpoints'])}")
            print(f"   Features: {len(info_data['features'])}")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 3. Testar listagem de modelos
    print("\n3. 🤖 TESTANDO LISTAGEM DE MODELOS")
    try:
        response = requests.get(f"{API_BASE_URL}/models/versions", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"   Modelos disponíveis: {len(models)}")
            for model in models:
                print(f"     - {model['version']} ({'ativo' if model['is_active'] else 'inativo'})")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 4. Testar previsão simples
    print("\n4. 🔮 TESTANDO PREVISÃO SIMPLES")
    try:
        prediction_request = {
            "fed_decision_date": "2025-01-29",
            "fed_move_bps": 25,
            "fed_move_dir": 1,
            "horizons_months": [1, 3, 6, 12],
            "regime_hint": "normal"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/predict/selic-from-fed",
            headers=headers,
            json=prediction_request
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            prediction = response.json()
            print(f"   Movimento esperado: {prediction['expected_move_bps']} bps")
            print(f"   Horizonte: {prediction['horizon_months']}")
            print(f"   Probabilidade próximo Copom: {prediction['prob_move_within_next_copom']:.2%}")
            print(f"   CI 80%: {prediction['ci80_bps']}")
            print(f"   CI 95%: {prediction['ci95_bps']}")
            print(f"   Reuniões: {len(prediction['per_meeting'])}")
            print(f"   Distribuição: {len(prediction['distribution'])} pontos")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 5. Testar previsão em lote
    print("\n5. 📦 TESTANDO PREVISÃO EM LOTE")
    try:
        batch_request = {
            "scenarios": [
                {
                    "fed_decision_date": "2025-01-29",
                    "fed_move_bps": 25,
                    "fed_move_dir": 1,
                    "regime_hint": "normal"
                },
                {
                    "fed_decision_date": "2025-01-29",
                    "fed_move_bps": 0,
                    "fed_move_dir": 0,
                    "regime_hint": "normal"
                }
            ]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/predict/selic-from-fed/batch",
            headers=headers,
            json=batch_request
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            batch_result = response.json()
            print(f"   Cenários processados: {batch_result['batch_metadata']['total_scenarios']}")
            print(f"   Sucessos: {batch_result['batch_metadata']['successful_predictions']}")
            print(f"   Erros: {batch_result['batch_metadata']['errors']}")
            print(f"   Tempo: {batch_result['batch_metadata']['processing_time_ms']}ms")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 6. Testar cenários de exemplo
    print("\n6. 📝 TESTANDO CENÁRIOS DE EXEMPLO")
    try:
        response = requests.get(f"{API_BASE_URL}/predict/scenarios", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            scenarios = response.json()
            print(f"   Cenários disponíveis: {scenarios['total']}")
            for scenario in scenarios['scenarios']:
                print(f"     - {scenario['name']}")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 7. Testar regras de validação
    print("\n7. ✅ TESTANDO REGRAS DE VALIDAÇÃO")
    try:
        response = requests.get(f"{API_BASE_URL}/predict/validation-rules", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            rules = response.json()
            print(f"   Regras definidas: {len(rules['validation_rules'])}")
            for field, rule in rules['validation_rules'].items():
                print(f"     - {field}: {rule['description']}")
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # 8. Testar erros de validação
    print("\n8. ❌ TESTANDO ERROS DE VALIDAÇÃO")
    
    # Teste 1: BPS inválido (não múltiplo de 25)
    try:
        invalid_request = {
            "fed_decision_date": "2025-01-29",
            "fed_move_bps": 30,  # Inválido
            "fed_move_dir": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/predict/selic-from-fed",
            headers=headers,
            json=invalid_request
        )
        
        print(f"   BPS inválido (30): Status {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"     Erro: {error_data.get('message', 'Erro desconhecido')}")
    except Exception as e:
        print(f"   Erro no teste de BPS inválido: {e}")
    
    # Teste 2: Data futura inválida
    try:
        invalid_request = {
            "fed_decision_date": "2030-01-29",  # Muito futuro
            "fed_move_bps": 25,
            "fed_move_dir": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/predict/selic-from-fed",
            headers=headers,
            json=invalid_request
        )
        
        print(f"   Data futura inválida: Status {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"     Erro: {error_data.get('message', 'Erro desconhecido')}")
    except Exception as e:
        print(f"   Erro no teste de data futura: {e}")
    
    # 9. Testar sem autenticação
    print("\n9. 🔐 TESTANDO SEM AUTENTICAÇÃO")
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/selic-from-fed",
            json=prediction_request
        )
        print(f"   Sem API Key: Status {response.status_code}")
        if response.status_code == 401:
            print("     ✅ Autenticação funcionando")
        else:
            print("     ❌ Autenticação não funcionando")
    except Exception as e:
        print(f"   Erro no teste de autenticação: {e}")
    
    print("\n" + "=" * 50)
    print("✅ TESTE DA API CONCLUÍDO!")

if __name__ == "__main__":
    test_api()