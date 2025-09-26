"""
API REST para Sistema de Análise de Spillovers Econômicos
MVP Comercial - Versão 1.0
"""
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import warnings
warnings.filterwarnings('ignore')

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from src.data.data_loader import EconomicDataLoader
from src.models.hybrid_model import BiasControlledHybridModel
from src.models.baseline_model import BaselineVARModel
from src.validation.scientific_validation import ScientificValidator

app = Flask(__name__)
CORS(app)

# Global variables para o modelo
model = None
baseline_model = None
data_loader = None
validator = None

# Inicializar modelos automaticamente
print("🔄 Inicializando modelos automaticamente...")
try:
    # Carregar dados
    data_loader = EconomicDataLoader()
    data = data_loader.load_brazil_us_data()
    data = data_loader.add_spillover_variable(data)
    
    # Treinar modelo híbrido
    model = BiasControlledHybridModel(
        var_lags=12,
        nn_hidden_layers=(50, 25),
        simple_weight=0.4,
        complex_weight=0.6
    )
    model.fit(data)
    
    # Treinar modelo baseline
    baseline_model = BaselineVARModel()
    baseline_model.fit(data)
    
    # Inicializar validador
    validator = ScientificValidator()
    
    print("✅ Modelos inicializados automaticamente!")
except Exception as e:
    print(f"⚠️  Erro na inicialização automática: {e}")
    print("🔄 Modelos serão inicializados na primeira requisição...")

def initialize_models():
    """Inicializar modelos uma única vez"""
    global model, baseline_model, data_loader, validator
    
    print("🔄 Inicializando modelos...")
    
    # Carregar dados
    data_loader = EconomicDataLoader()
    data = data_loader.load_brazil_us_data()
    data = data_loader.add_spillover_variable(data)
    
    # Treinar modelo híbrido
    model = BiasControlledHybridModel(
        var_lags=12,
        nn_hidden_layers=(50, 25),
        simple_weight=0.4,
        complex_weight=0.6
    )
    model.fit(data)
    
    # Treinar modelo baseline
    baseline_model = BaselineVARModel()
    baseline_model.fit(data)
    
    # Inicializar validador
    validator = ScientificValidator()
    
    print("✅ Modelos inicializados com sucesso!")

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/health')
def health_check():
    """Health check da API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'model_loaded': model is not None
    })

@app.route('/api/predict', methods=['POST'])
def predict_spillover():
    """
    Endpoint para predição de spillover
    
    Body:
    {
        "fed_rate": 5.25,
        "selic": 16.50,
        "include_uncertainty": true
    }
    """
    try:
        data = request.get_json()
        
        # Validar input
        if not data or 'fed_rate' not in data or 'selic' not in data:
            return jsonify({'error': 'fed_rate e selic são obrigatórios'}), 400
        
        fed_rate = float(data['fed_rate'])
        selic = float(data['selic'])
        include_uncertainty = data.get('include_uncertainty', True)
        
        # Validar ranges
        if not (0 <= fed_rate <= 20) or not (0 <= selic <= 30):
            return jsonify({'error': 'Taxas fora do range válido'}), 400
        
        # Preparar dados para predição
        X_new = pd.DataFrame({
            'fed_rate': [fed_rate],
            'selic': [selic]
        })
        
        # Fazer predição
        if include_uncertainty:
            prediction = model.predict_with_uncertainty(X_new)
            result = {
                'spillover_prediction': float(prediction['prediction']),
                'uncertainty': float(prediction['uncertainty']),
                'is_outlier': bool(prediction['is_outlier']),
                'high_uncertainty': bool(prediction['high_uncertainty']),
                'var_component': float(prediction.get('var_component', 0)),
                'nn_component': float(prediction.get('nn_component', 0))
            }
        else:
            prediction = model.predict(X_new)
            result = {
                'spillover_prediction': float(prediction['prediction']),
                'var_component': float(prediction.get('var_component', 0)),
                'nn_component': float(prediction.get('nn_component', 0))
            }
        
        # Adicionar metadados
        result.update({
            'timestamp': datetime.now().isoformat(),
            'input': {
                'fed_rate': fed_rate,
                'selic': selic
            },
            'model_info': {
                'type': 'Hybrid VAR + Neural Network',
                'validation_rmse': 0.2858,
                'validation_r2': 0.174,
                'diebold_mariano_pvalue': 0.0125
            }
        })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Erro na predição: {str(e)}'}), 500

@app.route('/api/batch_predict', methods=['POST'])
def batch_predict():
    """
    Endpoint para predições em lote
    
    Body:
    {
        "data": [
            {"fed_rate": 5.25, "selic": 16.50},
            {"fed_rate": 5.50, "selic": 16.75}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Campo data é obrigatório'}), 400
        
        predictions = []
        
        for item in data['data']:
            if 'fed_rate' not in item or 'selic' not in item:
                continue
                
            fed_rate = float(item['fed_rate'])
            selic = float(item['selic'])
            
            X_new = pd.DataFrame({
                'fed_rate': [fed_rate],
                'selic': [selic]
            })
            
            prediction = model.predict_with_uncertainty(X_new)
            
            predictions.append({
                'input': {'fed_rate': fed_rate, 'selic': selic},
                'spillover_prediction': float(prediction['prediction']),
                'uncertainty': float(prediction['uncertainty']),
                'is_outlier': bool(prediction['is_outlier']),
                'high_uncertainty': bool(prediction['high_uncertainty'])
            })
        
        return jsonify({
            'predictions': predictions,
            'count': len(predictions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro nas predições em lote: {str(e)}'}), 500

@app.route('/api/model_info')
def model_info():
    """Informações sobre o modelo"""
    return jsonify({
        'model_type': 'Hybrid VAR + Neural Network',
        'version': '1.0.0',
        'validation_metrics': {
            'rmse': 0.2858,
            'r2_mean': 0.174,
            'diebold_mariano_pvalue': 0.0125,
            'significant_improvement': True,
            'observations': 428,
            'period': '1990-2025'
        },
        'features': ['fed_rate', 'selic'],
        'output': 'spillover_prediction',
        'uncertainty_quantification': True,
        'outlier_detection': True,
        'scientific_validation': 'Approved'
    })

@app.route('/api/validation_report')
def validation_report():
    """Relatório de validação científica"""
    try:
        if validator is None:
            return jsonify({'error': 'Validador não inicializado'}), 500
        
        # Carregar dados para validação
        data = data_loader.load_brazil_us_data()
        data = data_loader.add_spillover_variable(data)
        
        # Executar validação
        validation_results = validator.comprehensive_validation(model, data, baseline_model)
        
        return jsonify({
            'validation_results': validation_results,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro na validação: {str(e)}'}), 500

@app.route('/api/historical_data')
def historical_data():
    """Dados históricos para visualização"""
    try:
        data = data_loader.load_brazil_us_data()
        data = data_loader.add_spillover_variable(data)
        
        # Converter para formato JSON
        historical = []
        for date, row in data.tail(100).iterrows():  # Últimos 100 períodos
            historical.append({
                'date': date.strftime('%Y-%m-%d'),
                'fed_rate': float(row['fed_rate']),
                'selic': float(row['selic']),
                'spillover': float(row['spillover'])
            })
        
        return jsonify({
            'historical_data': historical,
            'count': len(historical),
            'period': f"{data.index[0].strftime('%Y-%m')} a {data.index[-1].strftime('%Y-%m')}",
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar dados históricos: {str(e)}'}), 500

@app.route('/api/pricing')
def pricing_info():
    """Informações de pricing"""
    return jsonify({
        'tiers': [
            {
                'name': 'API Access',
                'price': 'R$ 999/mês',
                'features': [
                    'Predições de spillover',
                    'Quantificação de incerteza',
                    'Detecção de outliers',
                    'API REST completa',
                    'Suporte técnico'
                ],
                'target': 'Fintechs, startups quant'
            },
            {
                'name': 'Dashboard Enterprise',
                'price': 'R$ 4.999/mês',
                'features': [
                    'Interface visual completa',
                    'Relatórios automáticos',
                    'Alertas personalizados',
                    'Integração com sistemas',
                    'Suporte prioritário'
                ],
                'target': 'Bancos médios, asset management'
            },
            {
                'name': 'Custom Implementation',
                'price': 'R$ 50.000-200.000',
                'features': [
                    'Sistema customizado',
                    'Treinamento especializado',
                    'Integração completa',
                    'Suporte dedicado',
                    'SLA garantido'
                ],
                'target': 'Bancos grandes, Banco Central'
            }
        ],
        'contact': 'contato@spillover-ai.com',
        'demo_available': True
    })

if __name__ == '__main__':
    print("🚀 Iniciando API de Spillovers Econômicos...")
    initialize_models()
    print("🌐 API rodando em http://localhost:3000")
    app.run(debug=True, host='0.0.0.0', port=3000)
