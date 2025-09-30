"""
Schemas Pydantic para API FED-Selic
Definições de request/response para endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum

class FedMoveDirection(str, Enum):
    """Direção do movimento do Fed"""
    HAWKISH = "1"      # Aumento de juros
    NEUTRAL = "0"      # Manutenção
    DOVISH = "-1"      # Redução de juros

class RegimeHint(str, Enum):
    """Dicas de regime econômico"""
    NORMAL = "normal"
    STRESS = "stress"
    CRISIS = "crisis"
    RECOVERY = "recovery"

class PredictionRequest(BaseModel):
    """Request para previsão da Selic condicionada ao Fed"""
    
    fed_decision_date: str = Field(
        ...,
        description="Data da decisão do Fed (ISO-8601)",
        example="2025-10-29"
    )
    
    fed_move_bps: int = Field(
        ...,
        description="Magnitude do movimento do Fed em pontos-base",
        example=25,
        ge=-200,
        le=200
    )
    
    fed_move_dir: Optional[FedMoveDirection] = Field(
        None,
        description="Direção do movimento do Fed",
        example="1"
    )
    
    fed_surprise_bps: Optional[int] = Field(
        None,
        description="Componente surpresa do movimento (bps)",
        example=10,
        ge=-100,
        le=100
    )
    
    horizons_months: Optional[List[int]] = Field(
        [1, 3, 6, 12],
        description="Horizontes de previsão em meses",
        example=[1, 3, 6, 12],
        min_items=1,
        max_items=24
    )
    
    model_version: Optional[str] = Field(
        "latest",
        description="Versão do modelo a ser utilizada",
        example="v1.0.0"
    )
    
    regime_hint: Optional[RegimeHint] = Field(
        RegimeHint.NORMAL,
        description="Dica sobre o regime econômico atual",
        example="normal"
    )
    
    @validator('fed_move_bps')
    def validate_fed_move_bps(cls, v):
        """Validar que fed_move_bps é múltiplo de 25"""
        if v % 25 != 0:
            raise ValueError('fed_move_bps deve ser múltiplo de 25')
        return v
    
    @validator('fed_decision_date')
    def validate_fed_decision_date(cls, v):
        """Validar formato da data e se não é muito futuro"""
        try:
            date = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Verificar se não é muito futuro (máximo 1 ano)
            max_future = datetime.now().replace(tzinfo=date.tzinfo) + timedelta(days=365)
            if date > max_future:
                raise ValueError('fed_decision_date não pode ser mais de 1 ano no futuro')
        except ValueError as e:
            raise ValueError(f'fed_decision_date deve estar no formato ISO-8601: {e}')
        return v
    
    @validator('horizons_months')
    def validate_horizons_months(cls, v):
        """Validar horizontes estão no intervalo [1, 12]"""
        if v is not None:
            for horizon in v:
                if not (1 <= horizon <= 12):
                    raise ValueError('horizons_months deve estar no intervalo [1, 12]')
        return v

class CopomMeeting(BaseModel):
    """Reunião do Copom com previsão"""
    
    copom_date: str = Field(
        ...,
        description="Data da reunião do Copom",
        example="2025-11-05"
    )
    
    delta_bps: int = Field(
        ...,
        description="Mudança prevista na Selic (bps)",
        example=25
    )
    
    probability: float = Field(
        ...,
        description="Probabilidade do movimento ocorrer",
        example=0.41,
        ge=0.0,
        le=1.0
    )

class DistributionPoint(BaseModel):
    """Ponto da distribuição de probabilidade"""
    
    delta_bps: int = Field(
        ...,
        description="Mudança na Selic (bps)",
        example=25
    )
    
    probability: float = Field(
        ...,
        description="Probabilidade da mudança",
        example=0.52,
        ge=0.0,
        le=1.0
    )

class ModelMetadata(BaseModel):
    """Metadados do modelo utilizado"""
    
    version: str = Field(
        ...,
        description="Versão do modelo",
        example="v1.0.0"
    )
    
    trained_at: str = Field(
        ...,
        description="Data de treinamento do modelo",
        example="2025-09-25T12:00:00Z"
    )
    
    data_hash: str = Field(
        ...,
        description="Hash dos dados utilizados no treinamento",
        example="sha256:abcd1234..."
    )
    
    methodology: str = Field(
        ...,
        description="Metodologia utilizada",
        example="LP primary, BVAR fallback"
    )
    
    n_observations: Optional[int] = Field(
        None,
        description="Número de observações utilizadas no treinamento",
        example=20
    )
    
    r_squared: Optional[float] = Field(
        None,
        description="R² do modelo",
        example=0.65,
        ge=0.0,
        le=1.0
    )

class PredictionResponse(BaseModel):
    """Response da previsão da Selic"""
    
    expected_move_bps: int = Field(
        ...,
        description="Movimento esperado da Selic (bps)",
        example=25
    )
    
    horizon_months: str = Field(
        ...,
        description="Horizonte mais provável do movimento",
        example="1-3"
    )
    
    prob_move_within_next_copom: float = Field(
        ...,
        description="Probabilidade de movimento na próxima reunião do Copom",
        example=0.62,
        ge=0.0,
        le=1.0
    )
    
    ci80_bps: List[int] = Field(
        ...,
        description="Intervalo de confiança de 80% (bps)",
        example=[0, 50]
    )
    
    ci95_bps: List[int] = Field(
        ...,
        description="Intervalo de confiança de 95% (bps)",
        example=[-25, 75]
    )
    
    per_meeting: List[CopomMeeting] = Field(
        ...,
        description="Previsões por reunião do Copom",
        example=[
            {"copom_date": "2025-11-05", "delta_bps": 25, "probability": 0.41},
            {"copom_date": "2025-12-17", "delta_bps": 25, "probability": 0.21}
        ]
    )
    
    distribution: List[DistributionPoint] = Field(
        ...,
        description="Distribuição de probabilidade dos movimentos",
        example=[
            {"delta_bps": -25, "probability": 0.07},
            {"delta_bps": 0, "probability": 0.18},
            {"delta_bps": 25, "probability": 0.52},
            {"delta_bps": 50, "probability": 0.20}
        ]
    )
    
    model_metadata: ModelMetadata = Field(
        ...,
        description="Metadados do modelo utilizado"
    )
    
    rationale: str = Field(
        ...,
        description="Explicação da previsão",
        example="Resposta estimada positiva ao choque de +25 bps do Fed; maior massa de probabilidade no próximo Copom, alta incerteza devido à amostra curta."
    )
    
    confidence_level: str = Field(
        "medium",
        description="Nível de confiança da previsão",
        example="medium"
    )
    
    limitations: Optional[str] = Field(
        None,
        description="Limitações da previsão",
        example="Alta incerteza devido à amostra pequena (~20 observações)"
    )
    
    @validator('ci80_bps', 'ci95_bps')
    def validate_confidence_intervals(cls, v):
        """Validar intervalos de confiança"""
        if len(v) != 2:
            raise ValueError('Intervalos de confiança devem ter exatamente 2 valores [low, high]')
        if v[0] > v[1]:
            raise ValueError('Valor baixo deve ser menor ou igual ao valor alto')
        return v

class BatchPredictionRequest(BaseModel):
    """Request para previsões em lote"""
    
    scenarios: List[PredictionRequest] = Field(
        ...,
        description="Lista de cenários para previsão",
        min_items=1,
        max_items=10
    )

class BatchPredictionResponse(BaseModel):
    """Response para previsões em lote"""
    
    predictions: List[PredictionResponse] = Field(
        ...,
        description="Lista de previsões por cenário"
    )
    
    batch_metadata: Dict[str, Any] = Field(
        ...,
        description="Metadados do processamento em lote",
        example={
            "n_scenarios": 3,
            "processing_time_ms": 150,
            "model_version": "v1.0.0"
        }
    )

class ModelVersion(BaseModel):
    """Informações sobre versão do modelo"""
    
    version: str = Field(
        ...,
        description="Versão do modelo",
        example="v1.0.0"
    )
    
    trained_at: str = Field(
        ...,
        description="Data de treinamento",
        example="2025-09-25T12:00:00Z"
    )
    
    data_hash: str = Field(
        ...,
        description="Hash dos dados",
        example="sha256:abcd1234..."
    )
    
    methodology: str = Field(
        ...,
        description="Metodologia",
        example="LP primary, BVAR fallback"
    )
    
    n_observations: int = Field(
        ...,
        description="Número de observações",
        example=20
    )
    
    r_squared: float = Field(
        ...,
        description="R² do modelo",
        example=0.65
    )
    
    backtest_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="Métricas de backtest",
        example={
            "coverage_80": 0.85,
            "coverage_95": 0.92,
            "brier_score": 0.15
        }
    )

class HealthResponse(BaseModel):
    """Response do health check"""
    
    status: str = Field(
        ...,
        description="Status do serviço",
        example="healthy"
    )
    
    version: str = Field(
        ...,
        description="Versão da API",
        example="v1.0.0"
    )
    
    model_version: str = Field(
        ...,
        description="Versão do modelo ativo",
        example="v1.0.0"
    )
    
    uptime_seconds: float = Field(
        ...,
        description="Tempo de atividade em segundos",
        example=3600.0
    )
    
    latency_p50_ms: Optional[float] = Field(
        None,
        description="Latência P50 em milissegundos",
        example=45.2
    )
    
    latency_p95_ms: Optional[float] = Field(
        None,
        description="Latência P95 em milissegundos",
        example=120.5
    )
    
    requests_per_minute: Optional[float] = Field(
        None,
        description="Requests por minuto",
        example=15.3
    )

class ErrorResponse(BaseModel):
    """Response de erro"""
    
    error_code: str = Field(
        ...,
        description="Código do erro",
        example="invalid_request"
    )
    
    error_message: str = Field(
        ...,
        description="Mensagem de erro",
        example="fed_move_bps deve ser múltiplo de 25"
    )
    
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes adicionais do erro",
        example={"field": "fed_move_bps", "value": 30}
    )
    
    request_id: Optional[str] = Field(
        None,
        description="ID da requisição para rastreamento",
        example="req_123456789"
    )

# Códigos de erro padronizados conforme especificação
class ErrorCodes:
    """Códigos de erro padronizados da API"""
    INVALID_REQUEST = "invalid_request"           # 400
    UNSUPPORTED_VALUE = "unsupported_value"       # 422
    RATE_LIMITED = "rate_limited"                 # 429
    INTERNAL_ERROR = "internal_error"             # 500
    MODEL_UNAVAILABLE = "model_unavailable"       # 503
    AUTHENTICATION_FAILED = "authentication_failed"  # 401
    AUTHORIZATION_FAILED = "authorization_failed"     # 403
    VALIDATION_ERROR = "validation_error"         # 422
    DATA_UNAVAILABLE = "data_unavailable"         # 503

# Schemas para diferentes tipos de erro
class ValidationErrorDetails(BaseModel):
    """Detalhes de erro de validação"""
    field: str = Field(..., description="Campo com erro")
    value: Any = Field(..., description="Valor inválido")
    message: str = Field(..., description="Mensagem de erro específica")

class RateLimitDetails(BaseModel):
    """Detalhes de rate limiting"""
    limit: int = Field(..., description="Limite de requests")
    remaining: int = Field(..., description="Requests restantes")
    reset_time: datetime = Field(..., description="Tempo de reset do limite")

class ModelUnavailableDetails(BaseModel):
    """Detalhes quando modelo não está disponível"""
    requested_version: str = Field(..., description="Versão solicitada")
    available_versions: List[str] = Field(..., description="Versões disponíveis")
    estimated_availability: Optional[datetime] = Field(None, description="Estimativa de disponibilidade")

# Schema para resposta de erro padronizada
class StandardErrorResponse(BaseModel):
    """Resposta de erro padronizada"""
    error_code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes específicos do erro")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")
    request_id: Optional[str] = Field(None, description="ID da requisição")
    suggestions: Optional[List[str]] = Field(None, description="Sugestões de correção")

# Schema para resposta de sucesso padronizada
class StandardSuccessResponse(BaseModel):
    """Resposta de sucesso padronizada"""
    success: bool = Field(True, description="Indicador de sucesso")
    data: Any = Field(..., description="Dados da resposta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da resposta")
    request_id: Optional[str] = Field(None, description="ID da requisição")

# Schema para metadados de versão da API
class APIVersionInfo(BaseModel):
    """Informações da versão da API"""
    version: str = Field(..., description="Versão da API")
    build_date: str = Field(..., description="Data de build")
    git_commit: Optional[str] = Field(None, description="Commit Git")
    environment: str = Field(..., description="Ambiente (dev/staging/prod)")

# Schema para informações de rate limiting
class RateLimitInfo(BaseModel):
    """Informações de rate limiting"""
    limit: int = Field(..., description="Limite de requests")
    remaining: int = Field(..., description="Requests restantes")
    reset_time: datetime = Field(..., description="Tempo de reset")
    window_size: int = Field(..., description="Tamanho da janela em segundos")

# Schema para informações de autenticação
class AuthInfo(BaseModel):
    """Informações de autenticação"""
    api_key_id: str = Field(..., description="ID da chave API")
    permissions: List[str] = Field(..., description="Permissões da chave")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")
    rate_limit: RateLimitInfo = Field(..., description="Informações de rate limiting")
