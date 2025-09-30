"""
Probability Engine - Single Responsibility Principle
Engine responsável por conversão de previsões em probabilidades
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.interfaces import IProbabilityEngine
from src.core.exceptions import ProbabilityEngineError
from src.core.models import SelicPrediction, CopomMeeting, PredictionConfidence

class ProbabilityEngineService(IProbabilityEngine):
    """
    Engine de probabilidades
    
    Responsabilidades:
    - Converter previsões em probabilidades
    - Discretizar movimentos em 25 bps
    - Mapear para calendário do Copom
    - Calcular intervalos de confiança
    """
    
    def __init__(self, 
                 discretization_step: int = 25,
                 confidence_levels: List[float] = None):
        self.discretization_step = discretization_step
        self.confidence_levels = confidence_levels or [0.8, 0.95]
    
    async def convert_to_probabilities(self, 
                                     forecasts: Dict[str, Any], 
                                     copom_calendar: pd.DataFrame) -> SelicPrediction:
        """Converter previsões em probabilidades"""
        try:
            # Processar previsões por horizonte
            per_meeting = []
            distribution_points = []
            all_movements = []
            
            for horizon, forecast in forecasts.items():
                if not isinstance(forecast, dict):
                    continue
                
                # Obter previsão pontual e intervalos
                point_forecast = forecast.get('point_forecast', 0)
                ci_lower = forecast.get('ci_lower', point_forecast)
                ci_upper = forecast.get('ci_upper', point_forecast)
                
                # Discretizar movimento
                discretized_movement = self._discretize_movement(point_forecast)
                all_movements.append(discretized_movement)
                
                # Calcular probabilidade para este horizonte
                probability = self._calculate_horizon_probability(forecast)
                
                # Encontrar reunião do Copom correspondente
                copom_meeting = self._find_copom_meeting(horizon, copom_calendar)
                
                if copom_meeting:
                    per_meeting.append(CopomMeeting(
                        date=copom_meeting['date'],
                        expected_move_bps=discretized_movement,
                        probability=probability,
                        confidence_interval_80=(ci_lower, ci_upper),
                        confidence_interval_95=(ci_lower, ci_upper)
                    ))
            
            # Criar distribuição de probabilidade
            distribution_points = await self.discretize_movements(all_movements)
            
            # Calcular estatísticas gerais
            expected_move = self._calculate_expected_move(distribution_points)
            horizon_range = self._calculate_horizon_range(per_meeting)
            prob_next_copom = self._calculate_prob_next_copom(per_meeting)
            confidence_intervals = self._calculate_confidence_intervals(all_movements)
            
            # Determinar nível de confiança
            confidence_level = self._determine_confidence_level(forecasts)
            
            # Criar rationale
            rationale = self._generate_rationale(forecasts, expected_move, confidence_level)
            
            return SelicPrediction(
                expected_move_bps=expected_move,
                horizon_months=horizon_range,
                prob_move_within_next_copom=prob_next_copom,
                confidence_level=confidence_level,
                per_meeting=per_meeting,
                distribution=distribution_points,
                confidence_intervals=confidence_intervals,
                rationale=rationale,
                limitations="Alta incerteza devido à amostra pequena (~20 observações)"
            )
            
        except Exception as e:
            raise ProbabilityEngineError(f"Erro na conversão para probabilidades: {str(e)}")
    
    async def discretize_movements(self, movements: List[float]) -> List[Dict[str, Any]]:
        """Discretizar movimentos em múltiplos de 25 bps"""
        try:
            # Agrupar movimentos por valor discretizado
            discretized_counts = {}
            
            for movement in movements:
                discretized = self._discretize_movement(movement)
                discretized_counts[discretized] = discretized_counts.get(discretized, 0) + 1
            
            # Calcular probabilidades
            total_count = len(movements)
            distribution = []
            
            for movement_bps, count in discretized_counts.items():
                probability = count / total_count
                distribution.append({
                    "delta_bps": movement_bps,
                    "probability": round(probability, 3)
                })
            
            # Ordenar por movimento
            distribution.sort(key=lambda x: x["delta_bps"])
            
            return distribution
            
        except Exception as e:
            raise ProbabilityEngineError(f"Erro na discretização: {str(e)}")
    
    def _discretize_movement(self, movement: float) -> int:
        """Discretizar movimento para múltiplo de 25 bps"""
        return round(movement / self.discretization_step) * self.discretization_step
    
    def _calculate_horizon_probability(self, forecast: Dict[str, Any]) -> float:
        """Calcular probabilidade para horizonte específico"""
        # Lógica simplificada baseada na magnitude da previsão
        point_forecast = abs(forecast.get('point_forecast', 0))
        
        if point_forecast == 0:
            return 0.1  # Baixa probabilidade para movimento zero
        elif point_forecast <= 25:
            return 0.3  # Probabilidade média para movimentos pequenos
        elif point_forecast <= 50:
            return 0.6  # Alta probabilidade para movimentos médios
        else:
            return 0.8  # Muito alta probabilidade para movimentos grandes
    
    def _find_copom_meeting(self, horizon: str, copom_calendar: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Encontrar reunião do Copom para horizonte específico"""
        try:
            horizon_months = int(horizon.split('_')[1])
            
            # Calcular data alvo
            target_date = datetime.now() + timedelta(days=horizon_months * 30)
            
            # Encontrar reunião mais próxima
            if not copom_calendar.empty and 'date' in copom_calendar.columns:
                copom_dates = pd.to_datetime(copom_calendar['date'])
                closest_meeting = copom_calendar.iloc[copom_dates.sub(target_date).abs().idxmin()]
                
                return {
                    'date': closest_meeting['date'],
                    'meeting_number': closest_meeting.get('meeting_number', 1)
                }
            
            return None
            
        except Exception:
            return None
    
    def _calculate_expected_move(self, distribution: List[Dict[str, Any]]) -> int:
        """Calcular movimento esperado"""
        if not distribution:
            return 0
        
        expected = sum(point['delta_bps'] * point['probability'] for point in distribution)
        return self._discretize_movement(expected)
    
    def _calculate_horizon_range(self, per_meeting: List[CopomMeeting]) -> str:
        """Calcular range de horizonte mais provável"""
        if not per_meeting:
            return "1-3"
        
        # Encontrar reuniões com maior probabilidade
        sorted_meetings = sorted(per_meeting, key=lambda x: x.probability, reverse=True)
        
        if len(sorted_meetings) >= 2:
            return f"{sorted_meetings[0].date.month}-{sorted_meetings[1].date.month}"
        else:
            return f"{sorted_meetings[0].date.month}"
    
    def _calculate_prob_next_copom(self, per_meeting: List[CopomMeeting]) -> float:
        """Calcular probabilidade de movimento na próxima reunião do Copom"""
        if not per_meeting:
            return 0.0
        
        # Encontrar próxima reunião
        next_meeting = min(per_meeting, key=lambda x: x.date)
        return next_meeting.probability
    
    def _calculate_confidence_intervals(self, movements: List[float]) -> Dict[str, List[int]]:
        """Calcular intervalos de confiança"""
        if not movements:
            return {"ci80_bps": [0, 0], "ci95_bps": [0, 0]}
        
        movements_array = np.array(movements)
        
        # Calcular percentis
        ci80_lower = np.percentile(movements_array, 10)
        ci80_upper = np.percentile(movements_array, 90)
        ci95_lower = np.percentile(movements_array, 2.5)
        ci95_upper = np.percentile(movements_array, 97.5)
        
        return {
            "ci80_bps": [self._discretize_movement(ci80_lower), self._discretize_movement(ci80_upper)],
            "ci95_bps": [self._discretize_movement(ci95_lower), self._discretize_movement(ci95_upper)]
        }
    
    def _determine_confidence_level(self, forecasts: Dict[str, Any]) -> PredictionConfidence:
        """Determinar nível de confiança da previsão"""
        # Lógica simplificada baseada na consistência das previsões
        if not forecasts:
            return PredictionConfidence.LOW
        
        # Calcular variância das previsões
        predictions = [f.get('point_forecast', 0) for f in forecasts.values() if isinstance(f, dict)]
        
        if not predictions:
            return PredictionConfidence.LOW
        
        variance = np.var(predictions)
        
        if variance < 100:  # Baixa variância
            return PredictionConfidence.HIGH
        elif variance < 400:  # Variância média
            return PredictionConfidence.MEDIUM
        else:  # Alta variância
            return PredictionConfidence.LOW
    
    def _generate_rationale(self, forecasts: Dict[str, Any], 
                          expected_move: int, 
                          confidence_level: PredictionConfidence) -> str:
        """Gerar explicação da previsão"""
        rationale_parts = []
        
        # Movimento esperado
        if expected_move > 0:
            rationale_parts.append(f"Resposta estimada positiva de {expected_move} bps ao choque do Fed")
        elif expected_move < 0:
            rationale_parts.append(f"Resposta estimada negativa de {abs(expected_move)} bps ao choque do Fed")
        else:
            rationale_parts.append("Resposta neutra estimada ao choque do Fed")
        
        # Nível de confiança
        if confidence_level == PredictionConfidence.HIGH:
            rationale_parts.append("alta confiança na previsão")
        elif confidence_level == PredictionConfidence.MEDIUM:
            rationale_parts.append("confiança moderada na previsão")
        else:
            rationale_parts.append("baixa confiança devido à alta incerteza")
        
        # Limitações
        rationale_parts.append("alta incerteza devido à amostra curta (~20 observações)")
        
        return "; ".join(rationale_parts) + "."
