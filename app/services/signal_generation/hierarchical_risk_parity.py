"""
Hierarchical Risk Parity (HRP) - Alocação de Portfólio Robusta
Implementa clustering de correlação e alocação hierárquica de risco
Baseado em Lopez de Prado (2016)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class HierarchicalRiskParity:
    """
    Implementação do Hierarchical Risk Parity (HRP)
    Alocação de portfólio robusta baseada em clustering de correlação
    """
    
    def __init__(self, 
                 linkage_method: str = 'single',  # Método de linkage para clustering
                 distance_metric: str = 'euclidean'):  # Métrica de distância
        """
        Inicializa o HRP
        
        Args:
            linkage_method: Método de linkage ('single', 'complete', 'average', 'ward')
            distance_metric: Métrica de distância ('euclidean', 'correlation')
        """
        self.linkage_method = linkage_method
        self.distance_metric = distance_metric
        self.scaler = StandardScaler()
        
    def allocate_portfolio(self, 
                          returns: pd.DataFrame, 
                          regime_probabilities: Optional[pd.DataFrame] = None,
                          regime_weights: Optional[Dict] = None) -> Dict:
        """
        Aloca portfólio usando HRP
        
        Args:
            returns: DataFrame com retornos dos ativos
            regime_probabilities: Probabilidades de regime (opcional)
            regime_weights: Pesos por regime (opcional)
            
        Returns:
            Dicionário com alocação e métricas
        """
        try:
            # Preparar dados
            returns_clean = returns.dropna()
            if len(returns_clean) < 30:  # Mínimo de dados
                raise ValueError("Dados insuficientes para HRP")
            
            # Calcular matriz de correlação
            corr_matrix = returns_clean.corr()
            
            # Calcular matriz de distância
            distance_matrix = self._correlation_to_distance(corr_matrix)
            
            # Aplicar clustering hierárquico
            linkage_matrix = linkage(squareform(distance_matrix), method=self.linkage_method)
            
            # Determinar número de clusters
            n_clusters = min(4, len(returns_clean.columns))  # Máximo 4 clusters
            
            # Obter clusters
            clusters = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
            
            # Calcular alocação hierárquica
            allocation = self._hierarchical_allocation(
                returns_clean, 
                clusters, 
                regime_probabilities,
                regime_weights
            )
            
            # Calcular métricas
            metrics = self._calculate_allocation_metrics(allocation, returns_clean)
            
            return {
                'allocation': allocation,
                'clusters': clusters,
                'linkage_matrix': linkage_matrix,
                'correlation_matrix': corr_matrix,
                'distance_matrix': distance_matrix,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Erro na alocação HRP: {e}")
            return {'error': str(e)}
    
    def _correlation_to_distance(self, corr_matrix: pd.DataFrame) -> np.ndarray:
        """
        Converte matriz de correlação em matriz de distância
        """
        try:
            # Converter correlação para distância
            distance = np.sqrt(0.5 * (1 - corr_matrix.values))
            
            # Garantir que é simétrica
            distance = (distance + distance.T) / 2
            
            # Zerar diagonal
            np.fill_diagonal(distance, 0)
            
            return distance
            
        except Exception as e:
            logger.error(f"Erro na conversão correlação-distância: {e}")
            return np.eye(len(corr_matrix))
    
    def _hierarchical_allocation(self, 
                                returns: pd.DataFrame, 
                                clusters: np.ndarray,
                                regime_probabilities: Optional[pd.DataFrame] = None,
                                regime_weights: Optional[Dict] = None) -> Dict:
        """
        Calcula alocação hierárquica de risco
        """
        try:
            n_assets = len(returns.columns)
            allocation = np.zeros(n_assets)
            
            # Calcular volatilidade de cada ativo
            volatilities = returns.std() * np.sqrt(252)  # Anualizada
            
            # Calcular alocação por cluster
            unique_clusters = np.unique(clusters)
            
            for cluster_id in unique_clusters:
                # Ativos neste cluster
                cluster_assets = np.where(clusters == cluster_id)[0]
                cluster_returns = returns.iloc[:, cluster_assets]
                
                if len(cluster_assets) == 1:
                    # Cluster com um ativo
                    allocation[cluster_assets[0]] = 1.0 / len(unique_clusters)
                else:
                    # Cluster com múltiplos ativos - usar inversão da volatilidade
                    cluster_volatilities = volatilities.iloc[cluster_assets]
                    cluster_weights = 1.0 / cluster_volatilities
                    cluster_weights = cluster_weights / cluster_weights.sum()
                    
                    # Alocar dentro do cluster
                    for i, asset_idx in enumerate(cluster_assets):
                        allocation[asset_idx] = cluster_weights.iloc[i] / len(unique_clusters)
            
            # Aplicar ajustes por regime se disponível
            if regime_probabilities is not None and regime_weights is not None:
                allocation = self._adjust_for_regime(allocation, regime_probabilities, regime_weights)
            
            # Normalizar para soma 1
            allocation = allocation / allocation.sum()
            
            # Criar dicionário com alocação
            allocation_dict = {}
            for i, asset in enumerate(returns.columns):
                allocation_dict[asset] = allocation[i]
            
            return allocation_dict
            
        except Exception as e:
            logger.error(f"Erro na alocação hierárquica: {e}")
            return {}
    
    def _adjust_for_regime(self, 
                          base_allocation: np.ndarray, 
                          regime_probabilities: pd.DataFrame,
                          regime_weights: Dict) -> np.ndarray:
        """
        Ajusta alocação baseada nas probabilidades de regime
        """
        try:
            # Obter probabilidades do regime mais recente
            if len(regime_probabilities) > 0:
                latest_probs = regime_probabilities.iloc[-1]
                
                # Calcular alocação ponderada por regime
                adjusted_allocation = np.zeros_like(base_allocation)
                
                for regime, prob in latest_probs.items():
                    if regime.startswith('prob_') and prob > 0.1:  # Só considerar regimes com prob > 10%
                        regime_name = regime.replace('prob_', '')
                        if regime_name in regime_weights:
                            regime_allocation = np.array(list(regime_weights[regime_name].values()))
                            adjusted_allocation += prob * regime_allocation
                
                # Se nenhum regime foi considerado, usar alocação base
                if adjusted_allocation.sum() == 0:
                    adjusted_allocation = base_allocation
                else:
                    adjusted_allocation = adjusted_allocation / adjusted_allocation.sum()
                
                return adjusted_allocation
            else:
                return base_allocation
                
        except Exception as e:
            logger.error(f"Erro no ajuste por regime: {e}")
            return base_allocation
    
    def _calculate_allocation_metrics(self, allocation: Dict, returns: pd.DataFrame) -> Dict:
        """
        Calcula métricas da alocação
        """
        try:
            # Converter alocação para array
            allocation_array = np.array(list(allocation.values()))
            
            # Calcular retorno esperado do portfólio
            expected_returns = returns.mean() * 252  # Anualizado
            portfolio_return = np.sum(allocation_array * expected_returns)
            
            # Calcular volatilidade do portfólio
            cov_matrix = returns.cov() * 252  # Anualizada
            portfolio_variance = np.dot(allocation_array, np.dot(cov_matrix, allocation_array))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Calcular Sharpe ratio (assumindo risk-free rate = 5%)
            risk_free_rate = 0.05
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Calcular concentração (Herfindahl index)
            concentration = np.sum(allocation_array ** 2)
            
            # Calcular diversificação efetiva
            effective_diversification = 1.0 / concentration
            
            return {
                'expected_return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'concentration': concentration,
                'effective_diversification': effective_diversification,
                'max_allocation': np.max(allocation_array),
                'min_allocation': np.min(allocation_array)
            }
            
        except Exception as e:
            logger.error(f"Erro no cálculo de métricas: {e}")
            return {}
    
    def get_allocation_summary(self, results: Dict) -> Dict:
        """
        Gera resumo da alocação HRP
        """
        try:
            if 'error' in results:
                return results
            
            allocation = results['allocation']
            metrics = results['metrics']
            
            # Ordenar alocação por peso
            sorted_allocation = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
            
            summary = {
                'total_assets': len(allocation),
                'allocation': sorted_allocation,
                'metrics': metrics,
                'top_3_assets': sorted_allocation[:3],
                'concentration_risk': 'High' if metrics['concentration'] > 0.5 else 'Low'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo da alocação: {e}")
            return {'error': str(e)}
