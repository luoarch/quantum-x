"""
Pytest Fixtures Globais
Sprint 2 - Testing Setup
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from typing import Dict, Any

# Import da aplicação
from src.api.main import app
from src.api.schemas import (
    PredictionRequest, ModelMetadata, DistributionPoint, CopomMeeting
)
from src.models.bvar_minnesota import BVARMinnesota
from src.models.local_projections import LocalProjectionsForecaster


# ============================================================================
# FIXTURES DE DADOS
# ============================================================================

@pytest.fixture
def sample_fed_dates():
    """Datas de decisões do Fed (DatetimeIndex)"""
    base = datetime(2024, 1, 31)
    dates = [base + timedelta(days=45*i) for i in range(10)]
    return pd.DatetimeIndex(dates)


@pytest.fixture
def sample_selic_dates():
    """Datas de decisões do Copom (DatetimeIndex)"""
    base = datetime(2024, 2, 7)
    dates = [base + timedelta(days=45*i) for i in range(10)]
    return pd.DatetimeIndex(dates)


@pytest.fixture
def sample_fed_moves():
    """Movimentos do Fed (pandas Series)"""
    base = datetime(2024, 1, 31)
    dates = pd.DatetimeIndex([base + timedelta(days=45*i) for i in range(10)])
    return pd.Series([25, 0, -25, 25, 0, 25, -25, 0, 25, 0], index=dates)


@pytest.fixture
def sample_selic_moves():
    """Movimentos da Selic (pandas Series)"""
    base = datetime(2024, 2, 7)
    dates = pd.DatetimeIndex([base + timedelta(days=45*i) for i in range(10)])
    return pd.Series([0, 25, 0, 25, -25, 0, 25, 0, -25, 25], index=dates)


@pytest.fixture
def sample_dataset():
    """Dataset de exemplo para testes"""
    n = 20
    dates = pd.date_range('2023-01-01', periods=n, freq='45D')
    
    return pd.DataFrame({
        'date': dates,
        'fed_rate': 5.0 + np.random.randn(n) * 0.5,
        'selic_rate': 13.0 + np.random.randn(n) * 0.3,
        'fed_move': np.random.choice([0, 25, -25], n),
        'selic_move': np.random.choice([0, 25, -25, 50], n)
    })


# ============================================================================
# FIXTURES DE MODELOS
# ============================================================================

@pytest.fixture
def sample_bvar_model():
    """Modelo BVAR de exemplo (não treinado)"""
    return BVARMinnesota(
        n_lags=2,
        lambda1=0.2,
        lambda2=0.4,
        lambda3=1.5,
        random_state=42
    )


@pytest.fixture
def trained_bvar_model(sample_fed_moves, sample_selic_moves, 
                       sample_fed_dates, sample_selic_dates):
    """Modelo BVAR treinado"""
    model = BVARMinnesota(n_lags=2, random_state=42)
    model.prepare_data(sample_fed_moves, sample_selic_moves, 
                      sample_fed_dates, sample_selic_dates)
    model.estimate()
    return model


@pytest.fixture
def sample_lp_model():
    """Modelo LP de exemplo"""
    return LocalProjectionsForecaster(
        max_horizon=12,
        max_lags=2,
        alpha=0.1,
        regularization='ridge'
    )


# ============================================================================
# FIXTURES DE API
# ============================================================================

@pytest.fixture(scope="session")
def client():
    """
    Cliente de teste FastAPI (session-scoped)
    Usa modelos reais mas permite fake via env
    """
    import os
    os.environ.setdefault("ENVIRONMENT", "test")
    
    with TestClient(app) as c:
        # Garantir que modelos estão carregados (ou injetar fakes)
        app_instance = c.app
        
        # Se modelos não estão carregados, injetar fakes determinísticos
        if not getattr(app_instance.state, "models_loaded", False):
            # Criar modelos fake simples
            class FakeLP:
                def forecast(self, *args, **kwargs):
                    return {
                        "1": {"point": 12.5, "ci_lower": 0, "ci_upper": 25},
                        "3": {"point": 12.5, "ci_lower": -25, "ci_upper": 50}
                    }
                
                models = {1: None, 3: None, 6: None, 12: None}
            
            class FakeBVAR:
                stable = True
                eigs_F = np.array([0.4, 0.3])
                irf_fed_to_selic = np.array([0.51, 0.42, 0.35, 0.28])
                
                def conditional_forecast(self, fed_path_bps, horizon_months, **kwargs):
                    n = horizon_months
                    return {
                        "mean": np.array([12.5] * n),
                        "std": np.array([15.0] * n),
                        "ci95_lower": np.array([0] * n),
                        "ci95_upper": np.array([25] * n),
                        "samples": np.random.randn(100, n) * 15 + 12.5
                    }
            
            app_instance.state.model_lp = FakeLP()
            app_instance.state.model_bvar = FakeBVAR()
            app_instance.state.model_metadata = {
                "version": "vtest",
                "data_hash": "sha256:" + "00" * 32,
                "n_observations": 20,
                "methodology": "LP primary, BVAR fallback",
                "trained_at": "2025-09-30T00:00:00Z"
            }
            app_instance.state.model_version = "vtest"
            app_instance.state.models_loaded = True
        
        yield c


@pytest.fixture
def valid_api_key():
    """Chave API válida"""
    return "dev-key-123"  # Da config padrão


@pytest.fixture
def invalid_api_key():
    """Chave API inválida"""
    return "invalid-key-999"


@pytest.fixture
def auth_headers(valid_api_key):
    """Headers com autenticação válida"""
    return {
        "X-API-Key": valid_api_key,
        "Content-Type": "application/json"
    }


@pytest.fixture
def auth_headers_invalid(invalid_api_key):
    """Headers com autenticação inválida"""
    return {
        "X-API-Key": invalid_api_key,
        "Content-Type": "application/json"
    }


@pytest.fixture
def request_id_headers(auth_headers):
    """Headers com request_id para rastreamento"""
    return {
        **auth_headers,
        "X-Request-ID": "test-request-123"
    }


@pytest.fixture
def sample_prediction_request() -> Dict[str, Any]:
    """Request de previsão válido"""
    return {
        "fed_decision_date": "2025-10-29",
        "fed_move_bps": 25,
        "fed_move_dir": "1",
        "fed_surprise_bps": 10,
        "horizons_months": [1, 3, 6, 12],
        "model_version": "v1.0.2",
        "regime_hint": "normal"
    }


@pytest.fixture
def sample_batch_request(sample_prediction_request) -> Dict[str, Any]:
    """Request de batch válido"""
    scenarios = [
        {**sample_prediction_request, "fed_move_bps": 25},
        {**sample_prediction_request, "fed_move_bps": 0},
        {**sample_prediction_request, "fed_move_bps": -25}
    ]
    return {
        "scenarios": scenarios,
        "batch_id": "test_batch_001"
    }


# ============================================================================
# FIXTURES DE SCHEMAS
# ============================================================================

@pytest.fixture
def sample_model_metadata() -> Dict[str, Any]:
    """Metadata de modelo de exemplo"""
    return {
        "version": "v1.0.0",
        "trained_at": datetime.utcnow().isoformat() + 'Z',
        "data_hash": "sha256:abc123...",
        "methodology": "LP primary, BVAR fallback",
        "n_observations": 20,
        "r_squared": 0.65
    }


@pytest.fixture
def sample_distribution() -> list:
    """Distribuição de probabilidade de exemplo"""
    return [
        {"delta_bps": -25, "probability": 0.10},
        {"delta_bps": 0, "probability": 0.25},
        {"delta_bps": 25, "probability": 0.45},
        {"delta_bps": 50, "probability": 0.20}
    ]


@pytest.fixture
def sample_copom_meetings() -> list:
    """Reuniões do Copom de exemplo"""
    return [
        {"copom_date": "2025-11-05", "delta_bps": 25, "probability": 0.45},
        {"copom_date": "2025-12-10", "delta_bps": 25, "probability": 0.30}
    ]


# ============================================================================
# FIXTURES DE PERFORMANCE
# ============================================================================

@pytest.fixture
def performance_threshold():
    """Threshold de performance (p95 < 250ms)"""
    return 0.250  # 250ms


@pytest.fixture
def sample_latencies():
    """Latências de exemplo (em segundos)"""
    return np.array([0.045, 0.089, 0.123, 0.156, 0.201, 0.245])


# ============================================================================
# FIXTURES DE VALIDAÇÃO
# ============================================================================

@pytest.fixture
def validation_thresholds():
    """Thresholds de validação científica"""
    return {
        "ci95_coverage": 0.85,  # Cobertura mínima 85%
        "max_eigenvalue": 1.0,  # Estabilidade
        "min_r_squared": 0.30,  # R² mínimo
        "max_brier_score": 0.25  # Brier score máximo
    }


# ============================================================================
# FIXTURES DE MOCK
# ============================================================================

@pytest.fixture
def mock_model_artifacts(tmp_path):
    """Criar artefatos de modelo temporários"""
    model_dir = tmp_path / "models" / "v1.0.0"
    model_dir.mkdir(parents=True)
    
    # Criar arquivos mock
    (model_dir / "model_lp.pkl").write_text("mock lp model")
    (model_dir / "model_bvar.pkl").write_text("mock bvar model")
    (model_dir / "metadata.json").write_text('{"version": "v1.0.0"}')
    
    return model_dir


# ============================================================================
# AUTOUSE FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_random_seed():
    """Reset random seed antes de cada teste"""
    np.random.seed(42)
    yield
    # Teardown se necessário


@pytest.fixture(autouse=True)
def capture_warnings():
    """Capturar warnings durante testes"""
    import warnings
    warnings.simplefilter("always")
    yield


@pytest.fixture(autouse=True)
def clear_model_cache():
    """
    Limpar cache do ModelService entre testes
    Garante isolamento completo
    """
    from src.services.model_service import get_model_service
    
    # Cleanup ANTES do teste
    try:
        svc = get_model_service()
        if hasattr(svc, '_cache'):
            svc._cache.clear()
    except Exception:
        pass
    
    yield
    
    # Cleanup APÓS teste
    try:
        svc = get_model_service()
        if hasattr(svc, '_cache'):
            svc._cache.clear()
    except Exception:
        pass

