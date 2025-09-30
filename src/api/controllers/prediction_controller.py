"""
Prediction Controller - Single Responsibility Principle
Controller responsável pelos endpoints de previsão
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import uuid

from src.core.interfaces import IModelService, IDataRepository, IProbabilityEngine
from src.core.models import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest, 
    BatchPredictionResponse, FedDecision, FedMoveDirection
)
from src.core.exceptions import ValidationError, PredictionError
from src.api.schemas import (
    PredictionRequest as PredictionRequestSchema,
    PredictionResponse as PredictionResponseSchema,
    BatchPredictionRequest as BatchPredictionRequestSchema,
    BatchPredictionResponse as BatchPredictionResponseSchema,
    ErrorResponse
)

class PredictionController:
    """
    Controller para endpoints de previsão
    
    Responsabilidades:
    - POST /predict/selic-from-fed
    - POST /predict/selic-from-fed/batch
    - Validação de requests
    - Conversão de schemas
    """
    
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rotas do controller"""
        
        @self.router.post(
            "/predict/selic-from-fed",
            response_model=PredictionResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Previsão da Selic condicionada ao Fed",
            description="Retorna previsão probabilística da Selic baseada em movimento do Fed"
        )
        async def predict_selic_from_fed(
            request: PredictionRequestSchema,
            service_factory = Depends()
        ):
            """Endpoint principal de previsão"""
            try:
                # Converter schema para domain model
                fed_decision = FedDecision(
                    date=request.fed_decision_date,
                    move_bps=request.fed_move_bps,
                    direction=request.fed_move_dir,
                    surprise_bps=request.fed_surprise_bps
                )
                
                prediction_request = PredictionRequest(
                    fed_decision=fed_decision,
                    horizons_months=request.horizons_months,
                    model_version=request.model_version,
                    regime_hint=request.regime_hint,
                    request_id=str(uuid.uuid4())
                )
                
                # Obter serviço de previsão
                prediction_service = await service_factory.create_prediction_service()
                
                # Fazer previsão
                response = await prediction_service.predict_selic_from_fed(prediction_request)
                
                # Converter para schema de response
                return self._convert_to_response_schema(response)
                
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error_code": "VALIDATION_ERROR",
                        "error_message": e.message,
                        "error_details": e.details
                    }
                )
            except PredictionError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "PREDICTION_ERROR",
                        "error_message": e.message,
                        "error_details": e.details
                    }
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "INTERNAL_ERROR",
                        "error_message": "Erro interno do servidor",
                        "error_details": {"exception": str(e)}
                    }
                )
        
        @self.router.post(
            "/predict/selic-from-fed/batch",
            response_model=BatchPredictionResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Previsões em lote",
            description="Processa múltiplas previsões de forma eficiente"
        )
        async def predict_batch(
            request: BatchPredictionRequestSchema,
            service_factory = Depends()
        ):
            """Endpoint de previsões em lote"""
            try:
                # Converter schemas para domain models
                prediction_requests = []
                for scenario in request.scenarios:
                    fed_decision = FedDecision(
                        date=scenario.fed_decision_date,
                        move_bps=scenario.fed_move_bps,
                        direction=scenario.fed_move_dir,
                        surprise_bps=scenario.fed_surprise_bps
                    )
                    
                    prediction_request = PredictionRequest(
                        fed_decision=fed_decision,
                        horizons_months=scenario.horizons_months,
                        model_version=scenario.model_version,
                        regime_hint=scenario.regime_hint,
                        request_id=str(uuid.uuid4())
                    )
                    prediction_requests.append(prediction_request)
                
                # Obter serviço de previsão
                prediction_service = await service_factory.create_prediction_service()
                
                # Fazer previsões em lote
                responses = await prediction_service.predict_batch(prediction_requests)
                
                # Converter para schemas de response
                prediction_schemas = [self._convert_to_response_schema(r) for r in responses]
                
                # Criar response do lote
                batch_response = BatchPredictionResponseSchema(
                    predictions=prediction_schemas,
                    batch_metadata={
                        "n_scenarios": len(prediction_requests),
                        "success_count": len(responses),
                        "error_count": len(prediction_requests) - len(responses),
                        "processing_time_ms": sum(r.processing_time_ms for r in responses)
                    }
                )
                
                return batch_response
                
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error_code": "VALIDATION_ERROR",
                        "error_message": e.message,
                        "error_details": e.details
                    }
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error_code": "INTERNAL_ERROR",
                        "error_message": "Erro interno do servidor",
                        "error_details": {"exception": str(e)}
                    }
                )
    
    def _convert_to_response_schema(self, response: PredictionResponse) -> PredictionResponseSchema:
        """Converter domain model para schema de response"""
        return PredictionResponseSchema(
            expected_move_bps=response.prediction.expected_move_bps,
            horizon_months=response.prediction.horizon_months,
            prob_move_within_next_copom=response.prediction.prob_move_within_next_copom,
            ci80_bps=response.prediction.confidence_intervals.get('ci80_bps', [0, 0]),
            ci95_bps=response.prediction.confidence_intervals.get('ci95_bps', [0, 0]),
            per_meeting=[
                {
                    "copom_date": meeting.date.isoformat(),
                    "delta_bps": meeting.expected_move_bps,
                    "probability": meeting.probability
                }
                for meeting in response.prediction.per_meeting
            ],
            distribution=response.prediction.distribution,
            model_metadata={
                "version": response.model_metadata.version,
                "trained_at": response.model_metadata.trained_at.isoformat(),
                "data_hash": response.model_metadata.data_hash,
                "methodology": response.model_metadata.methodology,
                "n_observations": response.model_metadata.n_observations,
                "r_squared": response.model_metadata.r_squared
            },
            rationale=response.prediction.rationale,
            confidence_level=response.prediction.confidence_level.value,
            limitations=response.prediction.limitations
        )
