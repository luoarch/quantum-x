"""
Endpoints de previsão da Selic
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import time
import logging
from datetime import datetime

from ...api.schemas import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse,
    StandardErrorResponse, ErrorCodes, CopomMeeting, DistributionPoint, ModelMetadata
)
from ...core.config import get_settings
from ...services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependência para obter serviço de previsão
def get_prediction_service() -> PredictionService:
    """Obter serviço de previsão"""
    return PredictionService()

@router.post(
    "/selic-from-fed",
    response_model=PredictionResponse,
    summary="Prever movimento da Selic baseado no Fed",
    description="Previsão probabilística da Selic condicionada a um movimento do Fed"
)
async def predict_selic_from_fed(
    request: PredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Prever movimento da Selic baseado em um movimento do Fed.
    
    - **fed_decision_date**: Data da decisão do Fed (ISO-8601)
    - **fed_move_bps**: Magnitude do movimento em pontos-base (múltiplo de 25)
    - **fed_move_dir**: Direção do movimento (-1, 0, 1)
    - **fed_surprise_bps**: Componente surpresa (opcional)
    - **horizons_months**: Horizontes de previsão (1-12 meses)
    - **model_version**: Versão do modelo (opcional)
    - **regime_hint**: Dica de regime econômico (opcional)
    """
    try:
        start_time = time.time()
        
        # Validar request
        validation_result = await prediction_service.validate_request(request)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": ErrorCodes.VALIDATION_ERROR,
                    "message": validation_result["message"],
                    "details": validation_result.get("details")
                }
            )
        
        # Fazer previsão
        prediction = await prediction_service.predict_selic(request)
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Log da previsão
        logger.info(
            f"Previsão realizada: Fed {request.fed_move_bps}bps em {request.fed_decision_date}, "
            f"Selic esperada: {prediction.expected_move_bps}bps, "
            f"tempo: {processing_time:.3f}s"
        )
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na previsão: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante a previsão",
            details={"error": str(e)},
            request_id=getattr(request, 'request_id', None)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.post(
    "/selic-from-fed/batch",
    response_model=BatchPredictionResponse,
    summary="Previsões em lote",
    description="Múltiplas previsões da Selic para diferentes cenários do Fed"
)
async def predict_selic_batch(
    request: BatchPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Previsões em lote para múltiplos cenários.
    
    - **scenarios**: Lista de cenários para previsão
    - **batch_id**: ID do lote para rastreamento (opcional)
    """
    try:
        start_time = time.time()
        settings = get_settings()
        
        # Validar tamanho do lote
        if len(request.scenarios) > settings.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": ErrorCodes.VALIDATION_ERROR,
                    "message": f"Máximo {settings.MAX_BATCH_SIZE} cenários por lote",
                    "details": {"max_batch_size": settings.MAX_BATCH_SIZE}
                }
            )
        
        # Processar previsões
        predictions = []
        errors = []
        
        for i, scenario in enumerate(request.scenarios):
            try:
                # Validar cenário
                validation_result = await prediction_service.validate_request(scenario)
                if not validation_result["valid"]:
                    errors.append({
                        "index": i,
                        "error": validation_result["message"],
                        "details": validation_result.get("details")
                    })
                    continue
                
                # Fazer previsão
                prediction = await prediction_service.predict_selic(scenario)
                predictions.append(prediction)
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "details": {"exception_type": type(e).__name__}
                })
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Preparar metadados do lote
        batch_metadata = {
            "batch_id": request.batch_id,
            "total_scenarios": len(request.scenarios),
            "successful_predictions": len(predictions),
            "errors": len(errors),
            "processing_time_ms": round(processing_time * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log do lote
        logger.info(
            f"Lote processado: {len(predictions)}/{len(request.scenarios)} sucessos, "
            f"tempo: {processing_time:.3f}s"
        )
        
        return BatchPredictionResponse(
            predictions=predictions,
            batch_metadata=batch_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no processamento em lote: {str(e)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error_code=ErrorCodes.INTERNAL_ERROR,
            message="Erro interno durante o processamento em lote",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

@router.get(
    "/scenarios",
    summary="Cenários de exemplo",
    description="Lista de cenários de exemplo para teste da API"
)
async def get_example_scenarios():
    """
    Obter cenários de exemplo para teste da API.
    """
    scenarios = [
        {
            "name": "Fed +25 bps (Aumento padrão)",
            "description": "Aumento padrão de 25 pontos-base pelo Fed",
            "request": {
                "fed_decision_date": "2025-01-29",
                "fed_move_bps": 25,
                "fed_move_dir": 1,
                "horizons_months": [1, 3, 6, 12],
                "regime_hint": "normal"
            }
        },
        {
            "name": "Fed +50 bps (Aumento agressivo)",
            "description": "Aumento agressivo de 50 pontos-base pelo Fed",
            "request": {
                "fed_decision_date": "2025-01-29",
                "fed_move_bps": 50,
                "fed_move_dir": 1,
                "horizons_months": [1, 3, 6, 12],
                "regime_hint": "stress"
            }
        },
        {
            "name": "Fed -25 bps (Corte de juros)",
            "description": "Corte de 25 pontos-base pelo Fed",
            "request": {
                "fed_decision_date": "2025-01-29",
                "fed_move_bps": -25,
                "fed_move_dir": -1,
                "horizons_months": [1, 3, 6, 12],
                "regime_hint": "recovery"
            }
        },
        {
            "name": "Fed 0 bps (Manutenção)",
            "description": "Manutenção da taxa pelo Fed",
            "request": {
                "fed_decision_date": "2025-01-29",
                "fed_move_bps": 0,
                "fed_move_dir": 0,
                "horizons_months": [1, 3, 6, 12],
                "regime_hint": "normal"
            }
        }
    ]
    
    return {
        "scenarios": scenarios,
        "total": len(scenarios),
        "description": "Cenários de exemplo para teste da API de previsão FED-Selic"
    }

@router.get(
    "/validation-rules",
    summary="Regras de validação",
    description="Regras de validação para requests da API"
)
async def get_validation_rules():
    """
    Obter regras de validação para requests da API.
    """
    rules = {
        "fed_decision_date": {
            "type": "string",
            "format": "ISO-8601",
            "description": "Data da decisão do Fed",
            "constraints": [
                "Deve estar no formato ISO-8601",
                "Não pode ser mais de 1 ano no futuro"
            ]
        },
        "fed_move_bps": {
            "type": "integer",
            "description": "Magnitude do movimento em pontos-base",
            "constraints": [
                "Deve ser múltiplo de 25",
                "Range: -200 a +200 bps"
            ]
        },
        "fed_move_dir": {
            "type": "integer",
            "description": "Direção do movimento",
            "constraints": [
                "Valores permitidos: -1, 0, 1",
                "Opcional se fed_move_bps estiver presente"
            ]
        },
        "fed_surprise_bps": {
            "type": "integer",
            "description": "Componente surpresa em bps",
            "constraints": [
                "Opcional",
                "Range: -100 a +100 bps"
            ]
        },
        "horizons_months": {
            "type": "array",
            "description": "Horizontes de previsão em meses",
            "constraints": [
                "Valores entre 1 e 12",
                "Máximo 24 horizontes",
                "Padrão: [1, 3, 6, 12]"
            ]
        },
        "model_version": {
            "type": "string",
            "description": "Versão do modelo",
            "constraints": [
                "Opcional",
                "Padrão: versão mais recente"
            ]
        },
        "regime_hint": {
            "type": "string",
            "description": "Dica de regime econômico",
            "constraints": [
                "Valores: normal, stress, crisis, recovery",
                "Opcional",
                "Padrão: normal"
            ]
        }
    }
    
    return {
        "validation_rules": rules,
        "description": "Regras de validação para requests da API FED-Selic"
    }
