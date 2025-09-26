"""
Prediction Logger - Single Responsibility Principle
Responsável apenas por logar predições com contexto de network effects
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .types import ClientPrediction, ClientId
from .client_tracker import ClientTracker

class PredictionLogger:
    """
    Logger de predições com network effects - KISS + SOLID
    Single Responsibility: apenas logging de predições
    """
    
    def __init__(self, client_tracker: ClientTracker, model_version: str = "1.0.0"):
        self.client_tracker = client_tracker
        self.model_version = model_version
    
    def log_prediction(
        self,
        client_id: ClientId,
        input_data: Dict[str, float],
        prediction_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Loga uma predição com contexto de network effects
        
        Args:
            client_id: ID do cliente
            input_data: Dados de entrada (fed_rate, selic)
            prediction_result: Resultado da predição do modelo
            
        Returns:
            ID da predição ou None se erro
        """
        try:
            # Criar objeto de predição
            prediction = ClientPrediction(
                client_id=client_id,
                timestamp=datetime.now(),
                input_data=input_data,
                prediction=float(prediction_result['prediction']),
                uncertainty=float(prediction_result.get('uncertainty', 0.0)),
                is_outlier=bool(prediction_result.get('is_outlier', False)),
                high_uncertainty=bool(prediction_result.get('high_uncertainty', False)),
                model_version=self.model_version
            )
            
            # Registrar no tracker
            success = self.client_tracker.log_prediction(prediction)
            
            if success:
                # Gerar ID único para a predição
                prediction_id = f"{client_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
                return prediction_id
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao logar predição: {e}")
            return None
    
    def log_batch_predictions(
        self,
        client_id: ClientId,
        batch_data: list[Dict[str, Any]]
    ) -> list[str]:
        """
        Loga múltiplas predições em lote
        
        Args:
            client_id: ID do cliente
            batch_data: Lista de dados de predições
            
        Returns:
            Lista de IDs das predições
        """
        prediction_ids = []
        
        for data in batch_data:
            input_data = {
                'fed_rate': data['input']['fed_rate'],
                'selic': data['input']['selic']
            }
            
            prediction_result = {
                'prediction': data['spillover_prediction'],
                'uncertainty': data.get('uncertainty', 0.0),
                'is_outlier': data.get('is_outlier', False),
                'high_uncertainty': data.get('high_uncertainty', False)
            }
            
            pred_id = self.log_prediction(client_id, input_data, prediction_result)
            if pred_id:
                prediction_ids.append(pred_id)
        
        return prediction_ids
    
    def get_prediction_context(self, client_id: ClientId) -> Dict[str, Any]:
        """
        Obtém contexto de predições do cliente para network effects
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Contexto das predições do cliente
        """
        client_stats = self.client_tracker.get_client_stats(client_id)
        recent_predictions = self.client_tracker.get_client_predictions(client_id, days=30)
        
        if not client_stats:
            return {
                'is_new_client': True,
                'total_predictions': 0,
                'avg_uncertainty': 0.0,
                'outlier_rate': 0.0
            }
        
        return {
            'is_new_client': False,
            'total_predictions': client_stats['total_predictions'],
            'recent_predictions': client_stats['recent_predictions'],
            'avg_uncertainty': client_stats['avg_uncertainty'],
            'outlier_rate': client_stats['outlier_rate'],
            'last_prediction': client_stats.get('last_prediction'),
            'registered_at': client_stats.get('registered_at')
        }
