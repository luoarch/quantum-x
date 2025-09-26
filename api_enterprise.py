#!/usr/bin/env python3
"""
Enterprise API - PostgreSQL + Redis + RabbitMQ + Network Effects
Sistema completo de Network Effects Moats
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

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Enterprise imports
from src.enterprise import DatabaseManager, CacheManager, QueueManager
from src.enterprise.retrainer import NetworkEffectsRetrainer
from src.enterprise.config import config
from src.enterprise.models import Client, Prediction, Feedback

# Original model imports
from src.data.data_loader import EconomicDataLoader
from src.models.hybrid_model import BiasControlledHybridModel
from src.models.baseline_model import BaselineVARModel
from src.validation.comprehensive_validator import ComprehensiveValidator

app = Flask(__name__, template_folder='api/templates')
CORS(app)

# Global variables
model = None
baseline_model = None
data_loader = None
validator = None

# Enterprise components
db_manager = DatabaseManager()
cache_manager = CacheManager()
queue_manager = QueueManager()
retrainer = NetworkEffectsRetrainer()

print("🏗️ Inicializando Enterprise API...")

# Initialize models
try:
    print("🔄 Carregando dados econômicos...")
    data_loader = EconomicDataLoader()
    data = data_loader.load_brazil_us_data()
    data = data_loader.add_spillover_variable(data)
    
    print("🧠 Treinando modelo híbrido...")
    model = BiasControlledHybridModel(
        var_lags=12,
        nn_hidden_layers=(50, 25),
        simple_weight=0.4,
        complex_weight=0.6
    )
    model.fit(data)
    
    print("📊 Treinando modelo baseline...")
    baseline_model = BaselineVARModel()
    baseline_model.fit(data)
    
    print("🔬 Inicializando validador...")
    validator = ComprehensiveValidator()
    
    print("✅ Enterprise API inicializada com sucesso!")
    
except Exception as e:
    print(f"❌ Erro na inicialização: {e}")
    raise

# Health check
@app.route('/api/health')
def health_check():
    """Comprehensive health check"""
    try:
        db_healthy = db_manager.health_check()
        cache_healthy = cache_manager.health_check()
        queue_healthy = queue_manager.health_check()
        
        return jsonify({
            'status': 'healthy' if all([db_healthy, cache_healthy, queue_healthy]) else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0-enterprise',
            'components': {
                'database': 'healthy' if db_healthy else 'unhealthy',
                'cache': 'healthy' if cache_healthy else 'unhealthy',
                'queue': 'healthy' if queue_healthy else 'unhealthy',
                'model': 'loaded' if model is not None else 'not_loaded'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Client registration
@app.route('/api/enterprise/register', methods=['POST'])
def register_client_enterprise():
    """Register client with enterprise features"""
    try:
        data = request.get_json()
        
        if not data or 'client_id' not in data:
            return jsonify({'error': 'client_id é obrigatório'}), 400
        
        client_id = data['client_id']
        metadata = data.get('metadata', {})
        
        # Check if client exists
        existing_client = db_manager.get_client(client_id)
        if existing_client:
            return jsonify({'error': 'Cliente já existe'}), 409
        
        # Create client
        client_data = {
            'client_id': client_id,
            'institution': metadata.get('institution'),
            'client_type': metadata.get('type', 'unknown'),
            'metadata': metadata
        }
        
        client = db_manager.create_client(client_data)
        if not client:
            return jsonify({'error': 'Erro ao criar cliente'}), 500
        
        # Cache client stats
        cache_manager.cache_client_stats(client_id, {
            'total_predictions': 0,
            'total_feedback': 0,
            'avg_uncertainty': 0.0,
            'outlier_rate': 0.0
        })
        
        return jsonify({
            'message': 'Cliente registrado com sucesso',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao registrar cliente: {str(e)}'}), 500

# Enterprise prediction with network effects
@app.route('/api/enterprise/predict', methods=['POST'])
def predict_enterprise():
    """Enterprise prediction with full network effects"""
    try:
        data = request.get_json()
        
        if not data or 'client_id' not in data or 'fed_rate' not in data or 'selic' not in data:
            return jsonify({'error': 'client_id, fed_rate e selic são obrigatórios'}), 400
        
        client_id = data['client_id']
        fed_rate = float(data['fed_rate'])
        selic = float(data['selic'])
        include_uncertainty = data.get('include_uncertainty', True)
        
        # Validate ranges
        if not (0 <= fed_rate <= 20) or not (0 <= selic <= 30):
            return jsonify({'error': 'Taxas fora do range válido'}), 400
        
        # Check if client exists
        client = db_manager.get_client(client_id)
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        # Try network effects prediction first
        network_prediction = retrainer.predict_with_network_effects(fed_rate, selic)
        
        if 'error' not in network_prediction:
            # Use network effects prediction
            result = {
                'spillover_prediction': network_prediction['prediction'],
                'uncertainty': network_prediction['uncertainty'],
                'is_outlier': network_prediction['is_outlier'],
                'high_uncertainty': network_prediction['high_uncertainty'],
                'model_version': network_prediction['model_version'],
                'network_effects_enabled': True
            }
        else:
            # Fallback to original model
            X_new = pd.DataFrame({
                'fed_rate': [fed_rate],
                'selic': [selic]
            })
            
            if include_uncertainty:
                prediction = model.predict_with_uncertainty(X_new)
                result = {
                    'spillover_prediction': float(prediction['prediction']),
                    'uncertainty': float(prediction['uncertainty']),
                    'is_outlier': bool(prediction['is_outlier']),
                    'high_uncertainty': bool(prediction['high_uncertainty']),
                    'var_component': float(prediction.get('var_component', 0)),
                    'nn_component': float(prediction.get('nn_component', 0)),
                    'network_effects_enabled': False
                }
            else:
                prediction = model.predict(X_new)
                result = {
                    'spillover_prediction': float(prediction['prediction']),
                    'var_component': float(prediction.get('var_component', 0)),
                    'nn_component': float(prediction.get('nn_component', 0)),
                    'network_effects_enabled': False
                }
        
        # Generate prediction ID
        prediction_id = f"{client_id}_{int(datetime.now().timestamp())}_{np.random.randint(1000, 9999)}"
        
        # Store prediction in database
        prediction_data = {
            'client_id': client_id,
            'prediction_id': prediction_id,
            'fed_rate': fed_rate,
            'selic_rate': selic,
            'spillover_prediction': result['spillover_prediction'],
            'uncertainty': result.get('uncertainty', 0.0),
            'is_outlier': result.get('is_outlier', False),
            'high_uncertainty': result.get('high_uncertainty', False),
            'model_version': result.get('model_version', '1.0.0'),
            'var_component': result.get('var_component', 0.0),
            'nn_component': result.get('nn_component', 0.0),
            'network_tracked': True
        }
        
        db_manager.create_prediction(prediction_data)
        
        # Update client stats
        client_stats = cache_manager.get_client_stats(client_id) or {}
        client_stats['total_predictions'] = client_stats.get('total_predictions', 0) + 1
        client_stats['last_prediction'] = datetime.now().isoformat()
        cache_manager.cache_client_stats(client_id, client_stats)
        
        # Publish prediction for async processing
        queue_manager.publish_prediction(prediction_data)
        
        # Add prediction ID to result
        result['prediction_id'] = prediction_id
        result['timestamp'] = datetime.now().isoformat()
        result['client_id'] = client_id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Erro na predição: {str(e)}'}), 500

# Enterprise feedback
@app.route('/api/enterprise/feedback', methods=['POST'])
def submit_feedback_enterprise():
    """Submit feedback with enterprise features"""
    try:
        data = request.get_json()
        
        if not data or 'client_id' not in data or 'prediction_id' not in data:
            return jsonify({'error': 'client_id e prediction_id são obrigatórios'}), 400
        
        client_id = data['client_id']
        prediction_id = data['prediction_id']
        
        # Check if client exists
        client = db_manager.get_client(client_id)
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        # Create feedback record
        feedback_data = {
            'client_id': client.id,
            'prediction_id': prediction_id,
            'actual_outcome': data.get('actual_outcome'),
            'feedback_score': data.get('feedback_score'),
            'was_accurate': data.get('was_accurate'),
            'feedback_text': data.get('feedback_text')
        }
        
        feedback = db_manager.create_feedback(feedback_data)
        if not feedback:
            return jsonify({'error': 'Erro ao registrar feedback'}), 500
        
        # Update client stats
        client_stats = cache_manager.get_client_stats(client_id) or {}
        client_stats['total_feedback'] = client_stats.get('total_feedback', 0) + 1
        cache_manager.cache_client_stats(client_id, client_stats)
        
        return jsonify({
            'message': 'Feedback registrado com sucesso',
            'feedback_id': feedback.id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao submeter feedback: {str(e)}'}), 500

# Enterprise analytics
@app.route('/api/enterprise/analytics')
def get_analytics_enterprise():
    """Get comprehensive enterprise analytics"""
    try:
        # Try cache first
        cached_metrics = cache_manager.get_network_metrics()
        if cached_metrics:
            return jsonify(cached_metrics)
        
        # Calculate fresh metrics
        from sqlalchemy import func
        
        with db_manager.get_session() as session:
            # Get basic counts
            total_clients = session.query(Client).filter(Client.is_active == True).count()
            total_predictions = session.query(Prediction).count()
            
            # Get recent predictions (last 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_predictions = session.query(Prediction).filter(
                Prediction.created_at >= cutoff
            ).all()
            
            # Calculate metrics
            if recent_predictions:
                avg_uncertainty = np.mean([p.uncertainty for p in recent_predictions])
                outlier_rate = np.mean([p.is_outlier for p in recent_predictions])
                high_uncertainty_rate = np.mean([p.high_uncertainty for p in recent_predictions])
            else:
                avg_uncertainty = 0.0
                outlier_rate = 0.0
                high_uncertainty_rate = 0.0
            
            # Calculate health score
            health_score = min(100, (total_clients * 10) + (total_predictions / 10))
            
            # Calculate network strength
            client_diversity = min(1.0, total_clients / 50)
            prediction_volume = min(1.0, total_predictions / 1000)
            input_diversity = 0.5  # Simplified for now
            
            network_strength = (client_diversity * 0.4 + prediction_volume * 0.3 + input_diversity * 0.3)
            
            # Get client ranking
            client_ranking = []
            for client in session.query(Client).filter(Client.is_active == True).all():
                client_predictions = session.query(Prediction).filter(
                    Prediction.client_id == client.id
                ).all()
                
                if client_predictions:
                    contribution_score = len(client_predictions) / 100
                    client_ranking.append({
                        'client_id': client.client_id,
                        'contribution_score': contribution_score,
                        'total_predictions': len(client_predictions),
                        'avg_uncertainty': np.mean([p.uncertainty for p in client_predictions]),
                        'outlier_rate': np.mean([p.is_outlier for p in client_predictions])
                    })
            
            client_ranking.sort(key=lambda x: x['contribution_score'], reverse=True)
            
            # Prepare response
            analytics = {
                'network_health': {
                    'health_score': health_score,
                    'total_clients': total_clients,
                    'total_predictions': total_predictions,
                    'avg_uncertainty': avg_uncertainty,
                    'outlier_rate': outlier_rate,
                    'high_uncertainty_rate': high_uncertainty_rate,
                    'last_updated': datetime.now().isoformat()
                },
                'client_ranking': client_ranking[:10],
                'network_strength': {
                    'strength': network_strength,
                    'level': 'strong' if network_strength > 0.7 else 'moderate' if network_strength > 0.4 else 'weak',
                    'client_diversity': client_diversity,
                    'prediction_volume': prediction_volume,
                    'input_diversity': input_diversity,
                    'recommendations': [
                        'Aumentar número de clientes' if client_diversity < 0.5 else 'Diversidade de clientes adequada',
                        'Aumentar volume de predições' if prediction_volume < 0.5 else 'Volume de predições adequado'
                    ]
                },
                'prediction_trends': {
                    'trend': 'stable',
                    'prediction_volume': len(recent_predictions),
                    'avg_uncertainty_trend': 'stable',
                    'outlier_trend': 'stable',
                    'daily_avg_predictions': len(recent_predictions),
                    'period_days': 1
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the results
            cache_manager.cache_network_metrics(analytics)
            
            return jsonify(analytics)
            
    except Exception as e:
        return jsonify({'error': f'Erro ao obter analytics: {str(e)}'}), 500

# Retrain endpoint
@app.route('/api/enterprise/retrain', methods=['POST'])
def trigger_retrain_enterprise():
    """Trigger model retraining with network effects"""
    try:
        should_retrain, info = retrainer.should_retrain()
        
        if not should_retrain:
            return jsonify({
                'message': 'Retreinamento não necessário no momento',
                'reason': info.get('reason', 'Critérios não atendidos'),
                'info': info,
                'timestamp': datetime.now().isoformat()
            })
        
        # Publish retrain request to queue
        retrain_data = {
            'triggered_by': 'api_request',
            'timestamp': datetime.now().isoformat(),
            'info': info
        }
        
        success = queue_manager.publish_retrain_request(retrain_data)
        
        if success:
            return jsonify({
                'message': 'Solicitação de retreinamento enviada para processamento',
                'info': info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Erro ao enviar solicitação de retreinamento'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro no retreinamento: {str(e)}'}), 500

# Dashboard
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/enterprise')
def enterprise_dashboard():
    """Enterprise dashboard"""
    return render_template('network_dashboard.html')

if __name__ == '__main__':
    print("🚀 Iniciando Enterprise API...")
    print("🌐 API rodando em http://localhost:3000")
    print("📊 Dashboard: http://localhost:3000/enterprise")
    print("🔗 Health: http://localhost:3000/api/health")
    app.run(debug=True, host='0.0.0.0', port=3000)
