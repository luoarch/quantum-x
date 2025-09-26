"""
Client Tracker - Single Responsibility Principle
Responsável apenas por rastrear clientes e suas predições
"""
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from .types import ClientPrediction, ClientFeedback, ClientId, PredictionId

class ClientTracker:
    """
    Rastreia clientes e suas predições - KISS + SOLID
    Single Responsibility: apenas tracking de clientes
    """
    
    def __init__(self, data_dir: str = "data/network_effects"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos de dados simples (KISS)
        self.predictions_file = self.data_dir / "predictions.jsonl"
        self.feedback_file = self.data_dir / "feedback.jsonl"
        self.clients_file = self.data_dir / "clients.json"
        
        self._load_clients()
    
    def _load_clients(self) -> None:
        """Carrega dados de clientes existentes"""
        if self.clients_file.exists():
            with open(self.clients_file, 'r') as f:
                self.clients = json.load(f)
        else:
            self.clients = {}
    
    def _save_clients(self) -> None:
        """Salva dados de clientes"""
        with open(self.clients_file, 'w') as f:
            json.dump(self.clients, f, indent=2, default=str)
    
    def register_client(self, client_id: ClientId, metadata: Optional[Dict] = None) -> bool:
        """
        Registra novo cliente
        
        Args:
            client_id: ID único do cliente
            metadata: Dados adicionais do cliente
            
        Returns:
            True se registrado com sucesso
        """
        if client_id in self.clients:
            return False  # Cliente já existe
            
        self.clients[client_id] = {
            'registered_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'total_predictions': 0,
            'last_prediction': None
        }
        
        self._save_clients()
        return True
    
    def log_prediction(self, prediction: ClientPrediction) -> bool:
        """
        Registra predição de cliente
        
        Args:
            prediction: Dados da predição
            
        Returns:
            True se registrado com sucesso
        """
        try:
            # Atualizar contador de cliente
            if prediction.client_id not in self.clients:
                self.register_client(prediction.client_id)
            
            self.clients[prediction.client_id]['total_predictions'] += 1
            self.clients[prediction.client_id]['last_prediction'] = prediction.timestamp.isoformat()
            
            # Salvar predição em arquivo
            prediction_data = {
                'client_id': prediction.client_id,
                'timestamp': prediction.timestamp.isoformat(),
                'input_data': prediction.input_data,
                'prediction': prediction.prediction,
                'uncertainty': prediction.uncertainty,
                'is_outlier': prediction.is_outlier,
                'high_uncertainty': prediction.high_uncertainty,
                'model_version': prediction.model_version
            }
            
            with open(self.predictions_file, 'a') as f:
                f.write(json.dumps(prediction_data) + '\n')
            
            self._save_clients()
            return True
            
        except Exception as e:
            print(f"Erro ao registrar predição: {e}")
            return False
    
    def log_feedback(self, feedback: ClientFeedback) -> bool:
        """
        Registra feedback do cliente
        
        Args:
            feedback: Dados do feedback
            
        Returns:
            True se registrado com sucesso
        """
        try:
            feedback_data = {
                'client_id': feedback.client_id,
                'prediction_id': feedback.prediction_id,
                'actual_outcome': feedback.actual_outcome,
                'feedback_score': feedback.feedback_score,
                'was_accurate': feedback.was_accurate,
                'timestamp': feedback.timestamp.isoformat()
            }
            
            with open(self.feedback_file, 'a') as f:
                f.write(json.dumps(feedback_data) + '\n')
            
            return True
            
        except Exception as e:
            print(f"Erro ao registrar feedback: {e}")
            return False
    
    def get_client_predictions(self, client_id: ClientId, days: int = 30) -> List[Dict]:
        """
        Obtém predições de um cliente
        
        Args:
            client_id: ID do cliente
            days: Últimos N dias
            
        Returns:
            Lista de predições
        """
        if not self.predictions_file.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        predictions = []
        
        with open(self.predictions_file, 'r') as f:
            for line in f:
                try:
                    pred = json.loads(line.strip())
                    if pred['client_id'] == client_id:
                        pred_date = datetime.fromisoformat(pred['timestamp'])
                        if pred_date >= cutoff_date:
                            predictions.append(pred)
                except:
                    continue
        
        return predictions
    
    def get_all_predictions(self, days: int = 30) -> List[Dict]:
        """
        Obtém todas as predições dos últimos N dias
        
        Args:
            days: Últimos N dias
            
        Returns:
            Lista de todas as predições
        """
        if not self.predictions_file.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        predictions = []
        
        with open(self.predictions_file, 'r') as f:
            for line in f:
                try:
                    pred = json.loads(line.strip())
                    pred_date = datetime.fromisoformat(pred['timestamp'])
                    if pred_date >= cutoff_date:
                        predictions.append(pred)
                except:
                    continue
        
        return predictions
    
    def get_active_clients(self, days: int = 30) -> Set[ClientId]:
        """
        Obtém clientes ativos nos últimos N dias
        
        Args:
            days: Últimos N dias
            
        Returns:
            Set de clientes ativos
        """
        predictions = self.get_all_predictions(days)
        return {pred['client_id'] for pred in predictions}
    
    def get_client_stats(self, client_id: ClientId) -> Optional[Dict]:
        """
        Obtém estatísticas de um cliente
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Estatísticas do cliente ou None
        """
        if client_id not in self.clients:
            return None
        
        client_data = self.clients[client_id].copy()
        predictions = self.get_client_predictions(client_id)
        
        client_data.update({
            'recent_predictions': len(predictions),
            'avg_uncertainty': sum(p['uncertainty'] for p in predictions) / len(predictions) if predictions else 0,
            'outlier_rate': sum(1 for p in predictions if p['is_outlier']) / len(predictions) if predictions else 0
        })
        
        return client_data
