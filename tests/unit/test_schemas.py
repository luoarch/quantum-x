"""
Testes Unitários - Schemas Pydantic
Sprint 2 - Testing
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.api.schemas import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest,
    BatchPredictionResponse, DistributionPoint, CopomMeeting,
    ModelMetadata, BatchError, FedMoveDirection, RegimeHint
)


# ============================================================================
# TESTES: PredictionRequest
# ============================================================================

class TestPredictionRequest:
    """Testes de validação do PredictionRequest"""
    
    def test_valid_request(self):
        """✅ Request válido deve ser aceito"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=25,
            fed_move_dir="1",
            horizons_months=[1, 3, 6]
        )
        assert req.fed_move_bps == 25
        assert req.fed_move_dir == FedMoveDirection.HAWKISH
        assert len(req.horizons_months) == 3
    
    @pytest.mark.parametrize("bps", [25, 0, -50, 50, -25, 100])
    def test_fed_move_bps_valid_multiples_of_25(self, bps):
        """✅ fed_move_bps válidos (múltiplos de 25)"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=bps,
            horizons_months=[1]
        )
        assert req.fed_move_bps == bps
        assert req.fed_move_bps % 25 == 0
    
    @pytest.mark.parametrize("bps", [10, 30, -35, 15, 99])
    def test_fed_move_bps_invalid_not_multiple_of_25(self, bps):
        """❌ fed_move_bps inválidos (não múltiplos de 25)"""
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(
                fed_decision_date="2025-10-29",
                fed_move_bps=bps,
                horizons_months=[1]
            )
        assert "múltiplo de 25" in str(exc_info.value).lower()
    
    def test_fed_move_dir_consistency_hawkish(self):
        """✅ Consistência: bps > 0 com direção hawkish"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=25,
            fed_move_dir="1"
        )
        assert req.fed_move_bps == 25
        assert req.fed_move_dir == FedMoveDirection.HAWKISH
    
    def test_fed_move_dir_inconsistency(self):
        """❌ Inconsistência: bps > 0 com direção dovish"""
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(
                fed_decision_date="2025-10-29",
                fed_move_bps=25,  # Positivo
                fed_move_dir="-1"  # Dovish (negativo)
            )
        assert "inconsistente" in str(exc_info.value).lower()
    
    def test_horizons_months_range(self):
        """✅ Horizontes devem estar entre 1 e 12"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=25,
            horizons_months=[1, 6, 12]
        )
        assert all(1 <= h <= 12 for h in req.horizons_months)
    
    def test_horizons_months_invalid_range(self):
        """❌ Horizontes fora do range devem falhar"""
        with pytest.raises(ValidationError):
            PredictionRequest(
                fed_decision_date="2025-10-29",
                fed_move_bps=25,
                horizons_months=[1, 13]  # 13 > 12
            )
    
    def test_fed_decision_date_format(self):
        """✅ Data deve estar no formato ISO-8601"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=25
        )
        assert req.fed_decision_date == "2025-10-29"
    
    def test_fed_decision_date_too_far_future(self):
        """❌ Data não pode ser mais de 1 ano no futuro"""
        future_date = (datetime.now() + timedelta(days=400)).date().isoformat()
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(
                fed_decision_date=future_date,
                fed_move_bps=25
            )
        assert "1 ano" in str(exc_info.value).lower()
    
    def test_regime_hint_enum(self):
        """✅ regime_hint deve ser enum válido"""
        req = PredictionRequest(
            fed_decision_date="2025-10-29",
            fed_move_bps=25,
            regime_hint="stress"
        )
        assert req.regime_hint == RegimeHint.STRESS


# ============================================================================
# TESTES: DistributionPoint
# ============================================================================

class TestDistributionPoint:
    """Testes de validação do DistributionPoint"""
    
    def test_valid_distribution_point(self):
        """✅ Ponto de distribuição válido"""
        point = DistributionPoint(delta_bps=25, probability=0.45)
        assert point.delta_bps == 25
        assert point.probability == 0.45
    
    def test_delta_bps_must_be_multiple_of_25(self):
        """❌ delta_bps deve ser múltiplo de 25"""
        with pytest.raises(ValidationError):
            DistributionPoint(delta_bps=30, probability=0.5)
    
    def test_probability_bounds(self):
        """✅ Probabilidade deve estar entre 0 e 1"""
        point = DistributionPoint(delta_bps=25, probability=0.5)
        assert 0.0 <= point.probability <= 1.0
    
    def test_probability_invalid_negative(self):
        """❌ Probabilidade negativa deve falhar"""
        with pytest.raises(ValidationError):
            DistributionPoint(delta_bps=25, probability=-0.1)
    
    def test_probability_invalid_greater_than_one(self):
        """❌ Probabilidade > 1 deve falhar"""
        with pytest.raises(ValidationError):
            DistributionPoint(delta_bps=25, probability=1.1)


# ============================================================================
# TESTES: BatchError
# ============================================================================

class TestBatchError:
    """Testes de validação do BatchError"""
    
    def test_valid_batch_error(self):
        """✅ BatchError válido"""
        error = BatchError(
            index=1,
            error="fed_move_bps deve ser múltiplo de 25",
            details={"value": 30}
        )
        assert error.index == 1
        assert "múltiplo" in error.error
        assert error.details["value"] == 30
    
    def test_batch_error_without_details(self):
        """✅ BatchError sem details é opcional"""
        error = BatchError(
            index=0,
            error="Erro genérico"
        )
        assert error.details is None


# ============================================================================
# TESTES: BatchPredictionRequest
# ============================================================================

class TestBatchPredictionRequest:
    """Testes de validação do BatchPredictionRequest"""
    
    def test_valid_batch_request(self, sample_prediction_request):
        """✅ Batch request válido"""
        batch = BatchPredictionRequest(
            scenarios=[sample_prediction_request, sample_prediction_request],
            batch_id="batch_001"
        )
        assert len(batch.scenarios) == 2
        assert batch.batch_id == "batch_001"
    
    def test_batch_min_items(self):
        """❌ Batch deve ter pelo menos 1 cenário"""
        with pytest.raises(ValidationError):
            BatchPredictionRequest(scenarios=[])
    
    def test_batch_max_items(self, sample_prediction_request):
        """❌ Batch deve ter no máximo 10 cenários"""
        scenarios = [sample_prediction_request] * 11
        with pytest.raises(ValidationError):
            BatchPredictionRequest(scenarios=scenarios)


# ============================================================================
# TESTES: PredictionResponse
# ============================================================================

class TestPredictionResponse:
    """Testes de validação do PredictionResponse"""
    
    def test_ci_intervals_validation(self):
        """✅ Intervalos de confiança devem ter exatamente 2 valores"""
        # CI80 válido
        response = PredictionResponse(
            schema_version="v1.0",
            expected_move_bps=25,
            horizon_months="1-3",
            prob_move_within_next_copom=0.62,
            ci80_bps=[0, 50],
            ci95_bps=[-25, 75],
            per_meeting=[],
            distribution=[],
            model_metadata=ModelMetadata(
                version="v1.0.0",
                trained_at="2025-09-25T12:00:00Z",
                data_hash="sha256:abc",
                methodology="LP primary"
            ),
            rationale="Test"
        )
        assert len(response.ci80_bps) == 2
        assert len(response.ci95_bps) == 2
    
    def test_ci_intervals_must_be_ordered(self):
        """❌ Intervalos de confiança devem estar ordenados (low <= high)"""
        with pytest.raises(ValidationError):
            PredictionResponse(
                schema_version="v1.0",
                expected_move_bps=25,
                horizon_months="1-3",
                prob_move_within_next_copom=0.62,
                ci80_bps=[50, 0],  # Desordenado
                ci95_bps=[-25, 75],
                per_meeting=[],
                distribution=[],
                model_metadata=ModelMetadata(
                    version="v1.0.0",
                    trained_at="2025-09-25T12:00:00Z",
                    data_hash="sha256:abc",
                    methodology="LP primary"
                ),
                rationale="Test"
            )
    
    def test_schema_version_present(self):
        """✅ schema_version deve estar presente"""
        response = PredictionResponse(
            schema_version="v1.0",
            expected_move_bps=25,
            horizon_months="1-3",
            prob_move_within_next_copom=0.62,
            ci80_bps=[0, 50],
            ci95_bps=[-25, 75],
            per_meeting=[],
            distribution=[],
            model_metadata=ModelMetadata(
                version="v1.0.0",
                trained_at="2025-09-25T12:00:00Z",
                data_hash="sha256:abc",
                methodology="LP primary"
            ),
            rationale="Test"
        )
        assert response.schema_version == "v1.0"


# ============================================================================
# TESTES: ModelMetadata
# ============================================================================

class TestModelMetadata:
    """Testes de validação do ModelMetadata"""
    
    def test_valid_metadata(self):
        """✅ Metadata válido"""
        metadata = ModelMetadata(
            version="v1.0.2",
            trained_at="2025-09-25T12:00:00Z",
            data_hash="sha256:abc123...",
            methodology="LP primary, BVAR fallback",
            n_observations=20,
            r_squared=0.65
        )
        assert metadata.version == "v1.0.2"
        assert metadata.n_observations == 20
        assert 0 <= metadata.r_squared <= 1.0
    
    def test_r_squared_bounds(self):
        """✅ R² deve estar entre 0 e 1"""
        metadata = ModelMetadata(
            version="v1.0.0",
            trained_at="2025-09-25T12:00:00Z",
            data_hash="sha256:abc",
            methodology="LP",
            r_squared=0.75
        )
        assert 0 <= metadata.r_squared <= 1.0

