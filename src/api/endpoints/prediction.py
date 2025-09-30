"""
Endpoints de previsão da Selic
v2.0 - Integrado com modelos REAIS do app.state
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
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

# Dependência para obter serviço com modelos REAIS
def get_prediction_service(request: Request) -> PredictionService:
    """
    Obter serviço de previsão com modelos REAIS do app.state
    
    v2.0: Injeta modelos carregados no startup
    """
    # Obter modelos do app.state
    model_lp = getattr(request.app.state, 'model_lp', None)
    model_bvar = getattr(request.app.state, 'model_bvar', None)
    model_metadata = getattr(request.app.state, 'model_metadata', {})
    
    # Validar que modelos estão carregados
    if not model_lp and not model_bvar:
        logger.error("Modelos não carregados no app.state")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": ErrorCodes.MODEL_UNAVAILABLE,
                "message": "Modelos não disponíveis. API iniciando ou erro no carregamento."
            }
        )
    
    return PredictionService(
        model_lp=model_lp,
        model_bvar=model_bvar,
        model_metadata=model_metadata
    )

@router.post(
    "/selic-from-fed",
    response_model=PredictionResponse,
    responses={
        422: {"model": StandardErrorResponse, "description": "Erro de validação"},
        503: {"model": StandardErrorResponse, "description": "Modelo indisponível"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    },
    summary="Prever movimento da Selic baseado no Fed",
    description="Previsão probabilística da Selic condicionada a um movimento do Fed",
    response_description="Previsão com distribuição, intervalos de confiança e reuniões Copom"
)
async def predict_selic_from_fed(
    request_obj: Request,
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
        start_time = time.perf_counter()  # Mais preciso que time.time()
        request_id = getattr(request_obj.state, 'request_id', None)
        
        # Normalizar horizons (ordenar, remover duplicatas)
        if request.horizons_months:
            request.horizons_months = sorted(set(request.horizons_months))
        
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
        processing_time = time.perf_counter() - start_time
        
        # Log estruturado completo
        top_3_dist = sorted(
            [(d.delta_bps, d.probability) for d in prediction.distribution],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        logger.info(
            "Previsão realizada",
            extra={
                "request_id": request_id,
                "model_version": prediction.model_metadata.version,
                "fed_move_bps": request.fed_move_bps,
                "regime_hint": request.regime_hint,
                "horizons": request.horizons_months,
                "expected_selic_bps": prediction.expected_move_bps,
                "horizon_range": prediction.horizon_months,
                "ci95_amplitude": prediction.ci95_bps[1] - prediction.ci95_bps[0],
                "top_3_bins": top_3_dist,
                "processing_time_ms": round(processing_time * 1000, 2)
            }
        )
        
        # Criar resposta com header customizado
        from fastapi.responses import JSONResponse
        response = JSONResponse(
            content=prediction.model_dump(mode='json'),
            status_code=200
        )
        response.headers["X-Model-Version"] = prediction.model_metadata.version
        response.headers["X-Processing-Time-Ms"] = str(round(processing_time * 1000, 2))
        
        return response
        
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
            detail=error_response.model_dump(mode='json')
        )

@router.post(
    "/selic-from-fed/batch",
    response_model=BatchPredictionResponse,
    responses={
        413: {"model": StandardErrorResponse, "description": "Payload muito grande"},
        422: {"model": StandardErrorResponse, "description": "Erro de validação"},
        503: {"model": StandardErrorResponse, "description": "Modelo indisponível"},
        500: {"model": StandardErrorResponse, "description": "Erro interno"}
    },
    summary="Previsões em lote",
    description="Múltiplas previsões da Selic para diferentes cenários do Fed"
)
async def predict_selic_batch(
    request_obj: Request,
    request: BatchPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Previsões em lote para múltiplos cenários.
    
    - **scenarios**: Lista de cenários para previsão
    - **batch_id**: ID do lote para rastreamento (opcional)
    """
    try:
        start_time = time.perf_counter()
        settings = get_settings()
        request_id = getattr(request_obj.state, 'request_id', None)
        
        # Validar tamanho do lote (413 Payload Too Large)
        if len(request.scenarios) > settings.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error_code": "payload_too_large",
                    "message": f"Máximo {settings.MAX_BATCH_SIZE} cenários por lote",
                    "details": {
                        "max_batch_size": settings.MAX_BATCH_SIZE,
                        "received": len(request.scenarios)
                    }
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
        processing_time = time.perf_counter() - start_time
        
        # Preparar metadados do lote
        batch_metadata = {
            "batch_id": request.batch_id if hasattr(request, 'batch_id') else None,
            "total_scenarios": len(request.scenarios),
            "successful_predictions": len(predictions),
            "errors": len(errors),
            "processing_time_ms": round(processing_time * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log estruturado do lote
        logger.info(
            "Lote processado",
            extra={
                "request_id": request_id,
                "batch_id": batch_metadata["batch_id"],
                "total": len(request.scenarios),
                "successful": len(predictions),
                "failed": len(errors),
                "processing_time_ms": batch_metadata["processing_time_ms"]
            }
        )
        
        return BatchPredictionResponse(
            predictions=predictions,
            batch_metadata=batch_metadata,
            errors=errors if errors else None
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
            detail=error_response.model_dump(mode='json')
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
