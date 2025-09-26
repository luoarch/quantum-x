"""
Network Analytics - Single Responsibility Principle
Responsável apenas por analisar métricas de network effects
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .types import NetworkMetrics, ClientId
from .client_tracker import ClientTracker

class NetworkAnalytics:
    """
    Analytics de network effects - KISS + SOLID
    Single Responsibility: apenas análise de métricas
    """
    
    def __init__(self, client_tracker: ClientTracker):
        self.client_tracker = client_tracker
    
    def get_network_health(self) -> Dict[str, any]:
        """
        Obtém saúde geral do network effect
        
        Returns:
            Métricas de saúde do network
        """
        active_clients = self.client_tracker.get_active_clients(days=30)
        all_predictions = self.client_tracker.get_all_predictions(days=30)
        
        # Métricas básicas
        total_clients = len(active_clients)
        total_predictions = len(all_predictions)
        
        # Métricas de qualidade
        if all_predictions:
            avg_uncertainty = np.mean([p['uncertainty'] for p in all_predictions])
            outlier_rate = np.mean([p['is_outlier'] for p in all_predictions])
            high_uncertainty_rate = np.mean([p['high_uncertainty'] for p in all_predictions])
        else:
            avg_uncertainty = 0.0
            outlier_rate = 0.0
            high_uncertainty_rate = 0.0
        
        # Score de saúde (0-100)
        health_score = self._calculate_health_score(
            total_clients, total_predictions, avg_uncertainty, outlier_rate
        )
        
        return {
            'health_score': health_score,
            'total_clients': total_clients,
            'total_predictions': total_predictions,
            'avg_uncertainty': avg_uncertainty,
            'outlier_rate': outlier_rate,
            'high_uncertainty_rate': high_uncertainty_rate,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_client_ranking(self, limit: int = 10) -> List[Dict[str, any]]:
        """
        Ranking de clientes por contribuição ao network effect
        
        Args:
            limit: Número máximo de clientes no ranking
            
        Returns:
            Lista de clientes ordenada por contribuição
        """
        active_clients = self.client_tracker.get_active_clients(days=30)
        rankings = []
        
        for client_id in active_clients:
            stats = self.client_tracker.get_client_stats(client_id)
            if not stats:
                continue
            
            # Calcular score de contribuição
            contribution_score = self._calculate_contribution_score(stats)
            
            rankings.append({
                'client_id': client_id,
                'contribution_score': contribution_score,
                'total_predictions': stats['total_predictions'],
                'recent_predictions': stats['recent_predictions'],
                'avg_uncertainty': stats['avg_uncertainty'],
                'outlier_rate': stats['outlier_rate']
            })
        
        # Ordenar por score de contribuição
        rankings.sort(key=lambda x: x['contribution_score'], reverse=True)
        
        return rankings[:limit]
    
    def get_prediction_trends(self, days: int = 30) -> Dict[str, any]:
        """
        Análise de tendências das predições
        
        Args:
            days: Período de análise
            
        Returns:
            Tendências das predições
        """
        predictions = self.client_tracker.get_all_predictions(days)
        
        if not predictions:
            return {
                'trend': 'no_data',
                'prediction_volume': 0,
                'avg_uncertainty_trend': 'stable',
                'outlier_trend': 'stable'
            }
        
        # Converter para DataFrame para análise
        df = pd.DataFrame(predictions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Volume de predições
        daily_volume = df.groupby(df['timestamp'].dt.date).size()
        volume_trend = self._calculate_trend(daily_volume.values)
        
        # Tendência de incerteza
        daily_uncertainty = df.groupby(df['timestamp'].dt.date)['uncertainty'].mean()
        uncertainty_trend = self._calculate_trend(daily_uncertainty.values)
        
        # Tendência de outliers
        daily_outliers = df.groupby(df['timestamp'].dt.date)['is_outlier'].mean()
        outlier_trend = self._calculate_trend(daily_outliers.values)
        
        return {
            'trend': volume_trend,
            'prediction_volume': len(predictions),
            'avg_uncertainty_trend': uncertainty_trend,
            'outlier_trend': outlier_trend,
            'daily_avg_predictions': daily_volume.mean(),
            'period_days': days
        }
    
    def get_network_effect_strength(self) -> Dict[str, any]:
        """
        Calcula força do network effect
        
        Returns:
            Métricas de força do network effect
        """
        active_clients = self.client_tracker.get_active_clients(days=30)
        all_predictions = self.client_tracker.get_all_predictions(days=30)
        
        if not active_clients or not all_predictions:
            return {
                'strength': 0.0,
                'level': 'none',
                'recommendations': ['Aumentar número de clientes', 'Melhorar qualidade dos dados']
            }
        
        # Calcular força baseada em múltiplos fatores
        client_diversity = min(len(active_clients) / 20, 1.0)  # 20 clientes = 100%
        prediction_volume = min(len(all_predictions) / 1000, 1.0)  # 1000 predições = 100%
        
        # Diversidade de inputs
        fed_rates = [p['input_data']['fed_rate'] for p in all_predictions]
        selic_rates = [p['input_data']['selic'] for p in all_predictions]
        
        input_diversity = min(
            (np.std(fed_rates) + np.std(selic_rates)) / 5, 1.0
        )
        
        # Força total (média ponderada)
        strength = (
            client_diversity * 0.4 +
            prediction_volume * 0.3 +
            input_diversity * 0.3
        )
        
        # Classificar nível
        if strength >= 0.8:
            level = 'strong'
            recommendations = ['Manter qualidade', 'Expandir para novos mercados']
        elif strength >= 0.5:
            level = 'moderate'
            recommendations = ['Aumentar volume de dados', 'Melhorar diversidade de clientes']
        elif strength >= 0.2:
            level = 'weak'
            recommendations = ['Focar em aquisição de clientes', 'Melhorar qualidade dos dados']
        else:
            level = 'minimal'
            recommendations = ['Estratégia de aquisição agressiva', 'Melhorar produto']
        
        return {
            'strength': strength,
            'level': level,
            'client_diversity': client_diversity,
            'prediction_volume': prediction_volume,
            'input_diversity': input_diversity,
            'recommendations': recommendations
        }
    
    def _calculate_health_score(
        self, 
        clients: int, 
        predictions: int, 
        uncertainty: float, 
        outlier_rate: float
    ) -> float:
        """Calcula score de saúde do network (0-100)"""
        
        # Score baseado em volume
        volume_score = min((clients * 2) + (predictions / 10), 50)
        
        # Score baseado em qualidade
        quality_score = 50
        if uncertainty > 0.5:  # Alta incerteza é ruim
            quality_score -= min(uncertainty * 20, 20)
        if outlier_rate > 0.1:  # Muitos outliers é ruim
            quality_score -= min(outlier_rate * 100, 20)
        
        return min(volume_score + quality_score, 100)
    
    def _calculate_contribution_score(self, client_stats: Dict[str, any]) -> float:
        """Calcula score de contribuição de um cliente"""
        
        # Baseado em volume de predições
        volume_score = min(client_stats['total_predictions'] / 100, 1.0)
        
        # Penalizar alta incerteza e outliers
        quality_penalty = 0
        if client_stats['avg_uncertainty'] > 0.5:
            quality_penalty += 0.2
        if client_stats['outlier_rate'] > 0.1:
            quality_penalty += 0.2
        
        return max(volume_score - quality_penalty, 0)
    
    def _calculate_trend(self, values: np.ndarray) -> str:
        """Calcula tendência de uma série temporal"""
        if len(values) < 2:
            return 'stable'
        
        # Regressão linear simples
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
