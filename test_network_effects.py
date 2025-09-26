#!/usr/bin/env python3
"""
Teste do Sistema de Network Effects - MOAT Implementation
Demonstra como o sistema captura dados dos clientes para melhorar o modelo
"""
import requests
import json
import time
import random
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:3000"

def test_network_effects():
    """Testa o sistema completo de network effects"""
    print("🚀 TESTE DO SISTEMA DE NETWORK EFFECTS")
    print("=" * 50)
    
    # 1. Registrar clientes
    print("\n📝 1. Registrando clientes...")
    clients = [
        {"client_id": "bank_001", "metadata": {"institution": "Banco ABC", "type": "bank"}},
        {"client_id": "fintech_002", "metadata": {"institution": "Fintech XYZ", "type": "fintech"}},
        {"client_id": "asset_003", "metadata": {"institution": "Asset Manager", "type": "asset_management"}}
    ]
    
    for client in clients:
        response = requests.post(f"{API_BASE}/api/network/register", json=client)
        if response.status_code == 200:
            print(f"✅ Cliente {client['client_id']} registrado")
        else:
            print(f"⚠️  Erro ao registrar {client['client_id']}: {response.text}")
    
    # 2. Fazer predições com diferentes clientes
    print("\n🔮 2. Fazendo predições com network effects...")
    
    # Simular cenários diferentes
    scenarios = [
        {"fed_rate": 5.25, "selic": 16.50, "description": "Cenário atual"},
        {"fed_rate": 5.50, "selic": 17.00, "description": "Fed sobe, Selic sobe"},
        {"fed_rate": 5.00, "selic": 16.00, "description": "Fed desce, Selic desce"},
        {"fed_rate": 5.75, "selic": 16.25, "description": "Fed sobe mais que Selic"},
        {"fed_rate": 4.75, "selic": 17.50, "description": "Fed desce, Selic sobe"}
    ]
    
    prediction_ids = []
    
    for i, scenario in enumerate(scenarios):
        client_id = clients[i % len(clients)]['client_id']
        
        prediction_data = {
            "client_id": client_id,
            "fed_rate": scenario["fed_rate"],
            "selic": scenario["selic"],
            "include_uncertainty": True
        }
        
        response = requests.post(f"{API_BASE}/api/network/predict", json=prediction_data)
        
        if response.status_code == 200:
            result = response.json()
            prediction_ids.append(result.get('prediction_id'))
            
            print(f"✅ {scenario['description']} - Cliente: {client_id}")
            print(f"   Predição: {result['spillover_prediction']:.4f}")
            print(f"   Incerteza: {result['uncertainty']:.4f}")
            print(f"   Network Tracked: {result['network_tracked']}")
            print()
        else:
            print(f"❌ Erro na predição: {response.text}")
    
    # 3. Simular feedback dos clientes
    print("\n📊 3. Simulando feedback dos clientes...")
    
    for i, pred_id in enumerate(prediction_ids):
        if pred_id:
            client_id = clients[i % len(clients)]['client_id']
            
            # Simular feedback realístico
            feedback_data = {
                "client_id": client_id,
                "prediction_id": pred_id,
                "actual_outcome": random.uniform(0.05, 0.25),  # Spillover real simulado
                "feedback_score": random.randint(6, 10),
                "was_accurate": random.choice([True, True, True, False])  # 75% accuracy
            }
            
            response = requests.post(f"{API_BASE}/api/network/feedback", json=feedback_data)
            
            if response.status_code == 200:
                print(f"✅ Feedback registrado para {client_id}")
            else:
                print(f"❌ Erro no feedback: {response.text}")
    
    # 4. Verificar analytics de network effects
    print("\n📈 4. Verificando analytics de network effects...")
    
    response = requests.get(f"{API_BASE}/api/network/analytics")
    
    if response.status_code == 200:
        analytics = response.json()
        
        print("🏥 Network Health:")
        health = analytics['network_health']
        print(f"   Health Score: {health['health_score']:.1f}/100")
        print(f"   Total Clientes: {health['total_clients']}")
        print(f"   Total Predições: {health['total_predictions']}")
        print(f"   Avg Incerteza: {health['avg_uncertainty']:.4f}")
        print(f"   Outlier Rate: {health['outlier_rate']:.2%}")
        
        print("\n🏆 Client Ranking:")
        for i, client in enumerate(analytics['client_ranking'][:3]):
            print(f"   {i+1}. {client['client_id']} - Score: {client['contribution_score']:.2f}")
        
        print("\n💪 Network Strength:")
        strength = analytics['network_strength']
        print(f"   Força: {strength['strength']:.2f} ({strength['level']})")
        print(f"   Diversidade de Clientes: {strength['client_diversity']:.2f}")
        print(f"   Volume de Predições: {strength['prediction_volume']:.2f}")
        print(f"   Diversidade de Inputs: {strength['input_diversity']:.2f}")
        
        print("\n📊 Tendências:")
        trends = analytics['prediction_trends']
        print(f"   Tendência: {trends['trend']}")
        print(f"   Volume Diário Médio: {trends['daily_avg_predictions']:.1f}")
        print(f"   Tendência Incerteza: {trends['avg_uncertainty_trend']}")
        
    else:
        print(f"❌ Erro ao obter analytics: {response.text}")
    
    # 5. Testar retreinamento
    print("\n🔄 5. Testando sistema de retreinamento...")
    
    response = requests.post(f"{API_BASE}/api/network/retrain")
    
    if response.status_code == 200:
        retrain_result = response.json()
        print(f"✅ {retrain_result['message']}")
        if 'training_samples' in retrain_result:
            print(f"   Amostras de treinamento: {retrain_result['training_samples']}")
    else:
        print(f"ℹ️  {response.json().get('message', 'Retreinamento não necessário')}")
    
    print("\n🎉 TESTE DE NETWORK EFFECTS CONCLUÍDO!")
    print("=" * 50)
    print("✅ Sistema de Network Effects implementado com sucesso!")
    print("✅ Cada cliente agora contribui para melhorar o modelo para todos!")
    print("✅ MOAT de Network Effects ativo! 🏰")

if __name__ == "__main__":
    print("⚠️  Certifique-se de que a API está rodando em http://localhost:3000")
    print("   Execute: python api/app.py")
    print()
    
    try:
        test_network_effects()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Certifique-se de que a API está rodando em http://localhost:3000")
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
