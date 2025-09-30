"""
Serviço de previsão da Selic
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from ..api.schemas import (
    PredictionRequest, PredictionResponse, CopomMeeting, DistributionPoint, ModelMetadata
)
from ..core.config import get_settings
from .model_service import ModelService
from .data_service import DataService

logger = logging.getLogger(__name__)

class PredictionService:
    """Serviço para previsões da Selic"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_service = ModelService()
        self.data_service = DataService()
        
        # Cache de modelos
        self._model_cache = {}
        self._last_model_load = None
    
    async def validate_request(self, request: PredictionRequest) -> Dict[str, Any]:
        """Validar request de previsão"""
        try:
            # Validar data
            fed_date = datetime.fromisoformat(request.fed_decision_date.replace('Z', '+00:00'))
            now = datetime.now()
            
            if fed_date > now + timedelta(days=365):
                return {
                    "valid": False,
                    "message": "Data da decisão do Fed não pode ser mais de 1 ano no futuro",
                    "details": {"max_future_days": 365}
                }
            
            # Validar múltiplos de 25 bps
            if request.fed_move_bps % 25 != 0:
                return {
                    "valid": False,
                    "message": "fed_move_bps deve ser múltiplo de 25",
                    "details": {"value": request.fed_move_bps, "required_multiple": 25}
                }
            
            # Validar horizontes
            if request.horizons_months:
                for horizon in request.horizons_months:
                    if not (1 <= horizon <= 12):
                        return {
                            "valid": False,
                            "message": "horizons_months deve estar no intervalo [1, 12]",
                            "details": {"invalid_horizon": horizon, "valid_range": [1, 12]}
                        }
            
            # Validar direção se fornecida
            if request.fed_move_dir is not None:
                if request.fed_move_dir not in [-1, 0, 1]:
                    return {
                        "valid": False,
                        "message": "fed_move_dir deve ser -1, 0 ou 1",
                        "details": {"invalid_direction": request.fed_move_dir}
                    }
                
                # Verificar consistência com bps
                if request.fed_move_bps > 0 and request.fed_move_dir <= 0:
                    return {
                        "valid": False,
                        "message": "fed_move_dir deve ser 1 quando fed_move_bps > 0",
                        "details": {"bps": request.fed_move_bps, "dir": request.fed_move_dir}
                    }
                elif request.fed_move_bps < 0 and request.fed_move_dir >= 0:
                    return {
                        "valid": False,
                        "message": "fed_move_dir deve ser -1 quando fed_move_bps < 0",
                        "details": {"bps": request.fed_move_bps, "dir": request.fed_move_dir}
                    }
                elif request.fed_move_bps == 0 and request.fed_move_dir != 0:
                    return {
                        "valid": False,
                        "message": "fed_move_dir deve ser 0 quando fed_move_bps = 0",
                        "details": {"bps": request.fed_move_bps, "dir": request.fed_move_dir}
                    }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "message": f"Erro na validação: {str(e)}",
                "details": {"exception": type(e).__name__}
            }
    
    async def predict_selic(self, request: PredictionRequest) -> PredictionResponse:
        """Fazer previsão da Selic"""
        try:
            # Obter modelo
            model = await self._get_model(request.model_version)
            
            # Obter dados
            data = await self.data_service.get_prediction_data()
            
            # Fazer previsão usando o modelo
            prediction_result = await self._make_prediction(model, request, data)
            
            # Construir resposta
            response = self._build_response(prediction_result, request)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na previsão: {str(e)}", exc_info=True)
            raise
    
    async def _get_model(self, version: Optional[str] = None) -> Any:
        """Obter modelo (com cache)"""
        version = version or self.settings.DEFAULT_MODEL_VERSION
        
        # Verificar cache
        if version in self._model_cache:
            return self._model_cache[version]
        
        # Carregar modelo
        model = await self.model_service.load_model(version)
        self._model_cache[version] = model
        
        # Limpar cache se necessário
        if len(self._model_cache) > self.settings.MODEL_CACHE_SIZE:
            # Remover modelo mais antigo
            oldest_version = min(self._model_cache.keys())
            del self._model_cache[oldest_version]
        
        return model
    
    async def _make_prediction(self, model: Any, request: PredictionRequest, data: pd.DataFrame) -> Dict[str, Any]:
        """Fazer previsão usando o modelo"""
        # TODO: Implementar previsão real com LP/BVAR
        # Por enquanto, retornar previsão simulada
        
        fed_shock = request.fed_move_bps / 100  # Converter para decimal
        
        # Simular resposta da Selic (placeholder)
        expected_move = int(fed_shock * 100)  # Mesmo movimento em bps
        
        # Simular distribuição de probabilidade
        distribution = self._simulate_distribution(fed_shock)
        
        # Simular previsões por reunião do Copom
        per_meeting = self._simulate_copom_predictions(request)
        
        # Simular intervalos de confiança
        ci80, ci95 = self._simulate_confidence_intervals(expected_move)
        
        return {
            "expected_move_bps": expected_move,
            "horizon_months": "1-3",
            "prob_move_within_next_copom": 0.62,
            "ci80_bps": ci80,
            "ci95_bps": ci95,
            "per_meeting": per_meeting,
            "distribution": distribution,
            "rationale": f"Resposta estimada ao choque de {request.fed_move_bps} bps do Fed; maior massa de probabilidade no próximo Copom, alta incerteza devido à amostra curta."
        }
    
    def _simulate_distribution(self, fed_shock: float) -> List[DistributionPoint]:
        """Simular distribuição de probabilidade"""
        # Distribuição centrada no movimento esperado
        expected_bps = int(fed_shock * 100)
        
        # Valores possíveis (múltiplos de 25 bps)
        possible_values = list(range(-100, 101, 25))
        
        # Probabilidades (distribuição normal centrada no esperado)
        probabilities = []
        for value in possible_values:
            prob = np.exp(-((value - expected_bps) ** 2) / (2 * 25 ** 2))
            probabilities.append(prob)
        
        # Normalizar
        total_prob = sum(probabilities)
        probabilities = [p / total_prob for p in probabilities]
        
        # Criar pontos da distribuição
        distribution = []
        for value, prob in zip(possible_values, probabilities):
            if prob > 0.01:  # Só incluir probabilidades > 1%
                distribution.append(DistributionPoint(
                    delta_bps=value,
                    probability=round(prob, 3)
                ))
        
        return distribution
    
    def _simulate_copom_predictions(self, request: PredictionRequest) -> List[CopomMeeting]:
        """Simular previsões por reunião do Copom"""
        # Datas simuladas de reuniões do Copom
        copom_dates = [
            "2025-02-05", "2025-03-19", "2025-05-07", "2025-06-18",
            "2025-08-06", "2025-09-17", "2025-11-05", "2025-12-17"
        ]
        
        # Probabilidades simuladas
        probabilities = [0.41, 0.21, 0.15, 0.10, 0.08, 0.03, 0.01, 0.01]
        
        per_meeting = []
        for date, prob in zip(copom_dates[:4], probabilities[:4]):  # Primeiras 4 reuniões
            per_meeting.append(CopomMeeting(
                copom_date=date,
                delta_bps=request.fed_move_bps,
                probability=prob
            ))
        
        return per_meeting
    
    def _simulate_confidence_intervals(self, expected_move: int) -> tuple:
        """Simular intervalos de confiança"""
        # Intervalos baseados no movimento esperado
        margin_80 = 25
        margin_95 = 50
        
        ci80 = [max(-100, expected_move - margin_80), min(100, expected_move + margin_80)]
        ci95 = [max(-100, expected_move - margin_95), min(100, expected_move + margin_95)]
        
        return ci80, ci95
    
    def _build_response(self, prediction_result: Dict[str, Any], request: PredictionRequest) -> PredictionResponse:
        """Construir resposta da previsão"""
        # Metadados do modelo
        model_metadata = ModelMetadata(
            version=request.model_version or self.settings.DEFAULT_MODEL_VERSION,
            trained_at="2025-01-01T00:00:00Z",
            data_hash="sha256:placeholder",
            methodology=self.settings.DEFAULT_METHODOLOGY,
            n_observations=20,
            r_squared=0.65
        )
        
        return PredictionResponse(
            expected_move_bps=prediction_result["expected_move_bps"],
            horizon_months=prediction_result["horizon_months"],
            prob_move_within_next_copom=prediction_result["prob_move_within_next_copom"],
            ci80_bps=prediction_result["ci80_bps"],
            ci95_bps=prediction_result["ci95_bps"],
            per_meeting=prediction_result["per_meeting"],
            distribution=prediction_result["distribution"],
            model_metadata=model_metadata,
            rationale=prediction_result["rationale"],
            confidence_level="medium",
            limitations="Alta incerteza devido à amostra pequena (~20 observações)"
        )