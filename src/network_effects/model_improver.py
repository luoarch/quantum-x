"""
Model Improver - Single Responsibility Principle
Responsável apenas por melhorar o modelo com dados de network effects
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

from .types import RetrainConfig, NetworkMetrics, ClientId
from .client_tracker import ClientTracker

class ModelImprover(ABC):
    """
    Interface para melhoradores de modelo - Open/Closed Principle
    """
    
    @abstractmethod
    def should_retrain(self, config: RetrainConfig) -> bool:
        """Verifica se deve retreinar o modelo"""
        pass
    
    @abstractmethod
    def prepare_training_data(self, client_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara dados para treinamento"""
        pass
    
    @abstractmethod
    def calculate_improvement(self, old_accuracy: float, new_accuracy: float) -> float:
        """Calcula melhoria do modelo"""
        pass

class SpilloverModelImprover(ModelImprover):
    """
    Melhorador específico para modelo de spillovers - SOLID + KISS
    Single Responsibility: apenas melhoria do modelo de spillovers
    """
    
    def __init__(self, client_tracker: ClientTracker):
        self.client_tracker = client_tracker
        self.last_retrain = datetime.now()
        self.retrain_attempts = 0
    
    def should_retrain(self, config: RetrainConfig) -> bool:
        """
        Verifica se deve retreinar baseado em network effects
        
        Args:
            config: Configuração de retreinamento
            
        Returns:
            True se deve retreinar
        """
        # Verificar se passou tempo suficiente
        days_since_retrain = (datetime.now() - self.last_retrain).days
        if days_since_retrain < config.retrain_frequency_days:
            return False
        
        # Verificar se tem dados suficientes
        active_clients = self.client_tracker.get_active_clients(days=30)
        if len(active_clients) < config.min_clients:
            return False
        
        all_predictions = self.client_tracker.get_all_predictions(days=30)
        if len(all_predictions) < config.min_predictions:
            return False
        
        # Verificar tentativas máximas
        if self.retrain_attempts >= config.max_retrain_attempts:
            return False
        
        return True
    
    def prepare_training_data(self, client_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara dados de clientes para treinamento do modelo
        
        Args:
            client_data: Dados de predições dos clientes
            
        Returns:
            (X, y) para treinamento
        """
        if not client_data:
            return pd.DataFrame(), pd.Series()
        
        # Converter para DataFrame
        df = pd.DataFrame(client_data)
        
        # Extrair features de entrada
        X = pd.DataFrame([
            {
                'fed_rate': pred['input_data']['fed_rate'],
                'selic': pred['input_data']['selic']
            }
            for pred in client_data
        ])
        
        # Usar predições como target (para fine-tuning)
        y = df['prediction'].values
        
        return X, pd.Series(y)
    
    def calculate_improvement(self, old_accuracy: float, new_accuracy: float) -> float:
        """
        Calcula melhoria percentual do modelo
        
        Args:
            old_accuracy: Accuracy anterior
            new_accuracy: Nova accuracy
            
        Returns:
            Melhoria percentual
        """
        if old_accuracy == 0:
            return 0.0
        
        improvement = ((new_accuracy - old_accuracy) / old_accuracy) * 100
        return improvement
    
    def get_network_metrics(self) -> NetworkMetrics:
        """
        Obtém métricas de network effects
        
        Returns:
            Métricas de network effects
        """
        active_clients = self.client_tracker.get_active_clients(days=30)
        all_predictions = self.client_tracker.get_all_predictions(days=30)
        
        # Calcular força do network effect
        network_strength = self._calculate_network_strength(active_clients, all_predictions)
        
        return NetworkMetrics(
            total_clients=len(active_clients),
            total_predictions=len(all_predictions),
            accuracy_improvement=0.0,  # Será calculado após retreinamento
            model_version="1.0.0",
            last_retrain=self.last_retrain,
            network_effect_strength=network_strength
        )
    
    def _calculate_network_strength(self, clients: set, predictions: List[Dict]) -> float:
        """
        Calcula força do network effect baseado em diversidade de dados
        
        Args:
            clients: Set de clientes ativos
            predictions: Lista de predições
            
        Returns:
            Força do network effect (0-1)
        """
        if not clients or not predictions:
            return 0.0
        
        # Diversidade de clientes (mais clientes = maior network effect)
        client_diversity = min(len(clients) / 50, 1.0)  # Normalizado para 50 clientes
        
        # Diversidade de inputs (mais variação = melhor)
        if len(predictions) > 1:
            fed_rates = [p['input_data']['fed_rate'] for p in predictions]
            selic_rates = [p['input_data']['selic'] for p in predictions]
            
            fed_std = np.std(fed_rates)
            selic_std = np.std(selic_rates)
            
            input_diversity = min((fed_std + selic_std) / 10, 1.0)  # Normalizado
        else:
            input_diversity = 0.0
        
        # Network strength = média ponderada
        network_strength = (client_diversity * 0.6) + (input_diversity * 0.4)
        
        return min(network_strength, 1.0)
    
    def mark_retrain_completed(self, success: bool = True) -> None:
        """
        Marca retreinamento como completado
        
        Args:
            success: Se o retreinamento foi bem-sucedido
        """
        self.last_retrain = datetime.now()
        if success:
            self.retrain_attempts = 0
        else:
            self.retrain_attempts += 1
