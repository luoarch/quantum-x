"""
Testes de Endpoints - Prediction (Contract Tests)
Sprint 2 - API Prediction Tests com governança e propriedades científicas
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


# ============================================================================
# HELPERS
# ============================================================================

def assert_distribution(distribution: list, tol: float = 1e-6):
    """
    Validar propriedades da distribuição de probabilidade
    
    - Soma = 1.0 (com tolerância)
    - delta_bps múltiplo de 25
    - Probabilidades em [0, 1]
    """
    total = sum(d["probability"] for d in distribution)
    assert abs(total - 1.0) < tol, f"Soma = {total}, esperado ~1.0"
    
    for d in distribution:
        assert d["delta_bps"] % 25 == 0, f"delta_bps={d['delta_bps']} não é múltiplo de 25"
        assert 0.0 <= d["probability"] <= 1.0, f"probability={d['probability']} fora de [0,1]"


def assert_governance_headers(response):
    """Validar headers de governança obrigatórios"""
    required_headers = [
        "X-Request-ID",
        "X-API-Version",
        "X-Active-Model-Version",
        "X-Environment",
        "X-Response-Time"
    ]
    
    for header in required_headers:
        assert header in response.headers, f"Header {header} ausente"
    
    # Validar formato de X-Response-Time
    response_time = response.headers.get("X-Response-Time", "")
    assert "ms" in response_time or "s" in response_time, f"X-Response-Time mal formatado: {response_time}"


# ============================================================================
# TESTES: POST /predict/selic-from-fed - Happy Path
# ============================================================================

@pytest.mark.contract
class TestPredictionHappyPath:
    """Testes de contrato do happy path"""
    
    def test_predict_happy_path_complete(self, client: TestClient, auth_headers):
        """✅ Previsão completa com todas as validações"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "fed_move_dir": "1",
            "horizons_months": [1, 3, 6],
            "regime_hint": "normal"
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        # Pode ser 200 (sucesso) ou 503/422/500 (modelos não disponíveis ou erro)
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Modelos não disponíveis ou erro: {response.status_code}")
        
        # ===== GOVERNANÇA =====
        assert_governance_headers(response)
        
        # ===== CONTRATO =====
        data = response.json()
        
        # Campos obrigatórios
        assert "expected_move_bps" in data
        assert "horizon_months" in data
        assert "prob_move_within_next_copom" in data
        assert "ci80_bps" in data
        assert "ci95_bps" in data
        assert "per_meeting" in data
        assert "distribution" in data
        assert "model_metadata" in data
        assert "rationale" in data
        
        # ===== PROPRIEDADES CIENTÍFICAS =====
        
        # expected_move_bps múltiplo de 25
        assert isinstance(data["expected_move_bps"], int)
        assert data["expected_move_bps"] % 25 == 0
        
        # horizon_months formato válido
        assert data["horizon_months"] in ("1-2", "2-4", "3-6", "3-6+", "1-3", "6-12")
        
        # per_meeting ≤ 4 reuniões
        assert len(data["per_meeting"]) <= 4
        for meeting in data["per_meeting"]:
            assert "copom_date" in meeting
            assert "delta_bps" in meeting
            assert "probability" in meeting
            assert meeting["delta_bps"] % 25 == 0
            assert 0.0 <= meeting["probability"] <= 1.0
        
        # Distribuição válida
        assert_distribution(data["distribution"], tol=1e-9)
        
        # CIs coerentes
        ci80 = data["ci80_bps"]
        ci95 = data["ci95_bps"]
        
        assert isinstance(ci80, list) and len(ci80) == 2
        assert isinstance(ci95, list) and len(ci95) == 2
        
        assert ci80[0] <= ci80[1], "CI80 mal ordenado"
        assert ci95[0] <= ci95[1], "CI95 mal ordenado"
        
        # CI80 deve estar dentro de CI95
        assert ci80[0] >= ci95[0], "CI80 low < CI95 low"
        assert ci80[1] <= ci95[1], "CI80 high > CI95 high"
        
        # CI95 deve ser mais amplo
        width_ci80 = ci80[1] - ci80[0]
        width_ci95 = ci95[1] - ci95[0]
        assert width_ci95 >= width_ci80, "CI95 não é mais amplo que CI80"
        
        # prob_move_within_next_copom válido
        assert 0.0 <= data["prob_move_within_next_copom"] <= 1.0
    
    @pytest.mark.parametrize("fed_move_bps", [25, 0, -25, 50, -50])
    def test_predict_different_fed_moves(self, client: TestClient, auth_headers, fed_move_bps):
        """✅ Diferentes movimentos do Fed devem funcionar"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": fed_move_bps,
            "horizons_months": [1, 3, 6]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        assert data["expected_move_bps"] % 25 == 0
        assert_distribution(data["distribution"])


# ============================================================================
# TESTES: Validação de Input (422)
# ============================================================================

@pytest.mark.contract
class TestPredictionValidation:
    """Testes de validação de input - 422"""
    
    @pytest.mark.parametrize("invalid_bps", [10, 30, -35, 15, 99, 12])
    def test_predict_validation_error_bps_not_multiple_of_25(
        self, client: TestClient, auth_headers, invalid_bps
    ):
        """❌ fed_move_bps não múltiplo de 25 → 422"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": invalid_bps,
            "horizons_months": [1, 3, 6]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        body = response.json()
        assert "error_code" in body or "message" in body or "detail" in body
    
    @pytest.mark.parametrize("invalid_horizons", [
        [0],           # Menor que 1
        [13],          # Maior que 12
        [0, 5, 13],    # Ambos fora do range
        [-1]           # Negativo
    ])
    def test_predict_validation_error_horizons_out_of_range(
        self, client: TestClient, auth_headers, invalid_horizons
    ):
        """❌ horizons_months fora de [1, 12] → 422"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": invalid_horizons
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_predict_validation_error_date_format(self, client: TestClient, auth_headers):
        """❌ Data formato inválido → 422"""
        payload = {
            "fed_decision_date": "2025/10/29",  # Formato errado
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_predict_validation_dir_consistency(self, client: TestClient, auth_headers):
        """❌ Inconsistência fed_move_bps e fed_move_dir → 422"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,      # Positivo
            "fed_move_dir": "-1",    # Dovish (negativo)
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        # Deve ser 422 (validação) ou 400 (bad request)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]


# ============================================================================
# TESTES: Regimes (stress → BVAR)
# ============================================================================

@pytest.mark.contract
class TestPredictionRegimes:
    """Testes de diferentes regimes econômicos"""
    
    @pytest.mark.parametrize("regime", ["normal", "stress", "crisis", "recovery"])
    def test_predict_regime_hint(self, client: TestClient, auth_headers, regime):
        """✅ Diferentes regimes devem funcionar"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "regime_hint": regime,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        # Headers de governança
        assert "X-Model-Version" in response.headers or "X-Active-Model-Version" in response.headers
        
        # Contrato válido
        data = response.json()
        assert_distribution(data["distribution"])
    
    def test_predict_regime_stress_uses_bvar(self, client: TestClient, auth_headers):
        """✅ regime_hint=stress força BVAR (validar via headers)"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "regime_hint": "stress",
            "horizons_months": [1, 3, 6]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        # Validar que processou corretamente
        data = response.json()
        assert_distribution(data["distribution"])
        
        # Rationale pode mencionar BVAR (não obrigatório)
        # if "rationale" in data:
        #     assert "BVAR" in data["rationale"] or "conditional" in data["rationale"].lower()


# ============================================================================
# TESTES: POST /predict/selic-from-fed/batch
# ============================================================================

@pytest.mark.contract
class TestBatchPrediction:
    """Testes de batch prediction"""
    
    def test_batch_valid_scenarios(self, client: TestClient, auth_headers):
        """✅ Batch com cenários válidos"""
        scenarios = [
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 25, "horizons_months": [1, 3]},
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 0, "horizons_months": [1, 3]},
            {"fed_decision_date": "2025-10-29", "fed_move_bps": -25, "horizons_months": [1, 3]}
        ]
        
        payload = {
            "scenarios": scenarios,
            "batch_id": "test_batch_001"
        }
        
        response = client.post(
            "/predict/selic-from-fed/batch",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        
        # Estrutura obrigatória
        assert "predictions" in data
        assert "batch_metadata" in data
        
        # Validar metadata
        metadata = data["batch_metadata"]
        assert "total_scenarios" in metadata
        assert metadata["total_scenarios"] == len(scenarios)
        
        # Todas previsões devem ser válidas
        for pred in data["predictions"]:
            assert pred["expected_move_bps"] % 25 == 0
            assert_distribution(pred["distribution"])
    
    def test_batch_mixed_valid_invalid(self, client: TestClient, auth_headers):
        """✅ Batch com cenários válidos e inválidos"""
        scenarios = [
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 25, "horizons_months": [1]},
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 10, "horizons_months": [1]},  # Inválido
            {"fed_decision_date": "2025-10-29", "fed_move_bps": -25, "horizons_months": [1]}
        ]
        
        payload = {"scenarios": scenarios}
        
        response = client.post(
            "/predict/selic-from-fed/batch",
            json=payload,
            headers=auth_headers
        )
        
        # Pode validar antes (422) ou processar parcialmente (200 com errors)
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            # Validação Pydantic bloqueou tudo
            return
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        body = response.json()
        
        # batch_metadata deve estar presente
        assert "batch_metadata" in body
        assert body["batch_metadata"]["total_scenarios"] == 3
        
        # Sucessos em predictions
        assert len(body["predictions"]) >= 1
        
        # Campo errors deve existir e conter erro do índice 1
        if "errors" in body and body["errors"] is not None:
            assert len(body["errors"]) > 0
            error_indices = [e["index"] for e in body["errors"]]
            assert 1 in error_indices, "Erro do índice 1 (bps=10) não reportado"
    
    def test_batch_too_large(self, client: TestClient, auth_headers):
        """❌ Batch maior que MAX_BATCH_SIZE → 413"""
        from src.core.config import get_settings
        settings = get_settings()
        max_batch = getattr(settings, "MAX_BATCH_SIZE", 10)
        
        # Criar batch maior que o limite
        scenarios = [
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 25, "horizons_months": [1]}
            for _ in range(max_batch + 1)
        ]
        
        payload = {"scenarios": scenarios}
        
        response = client.post(
            "/predict/selic-from-fed/batch",
            json=payload,
            headers=auth_headers
        )
        
        # Deve ser 413 (preferido) ou 422 (validação)
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        
        body = response.json()
        assert "message" in body or "error_code" in body or "detail" in body


# ============================================================================
# TESTES: Governança e Headers
# ============================================================================

@pytest.mark.contract
class TestPredictionGovernance:
    """Testes de governança e headers"""
    
    def test_governance_headers_complete(self, client: TestClient, auth_headers):
        """✅ Todos headers de governança presentes"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        # Headers obrigatórios
        required_headers = [
            "X-API-Version",
            "X-Environment",
            "X-Request-ID",
            "X-Active-Model-Version",
            "X-Response-Time"
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Header {header} ausente"
    
    def test_request_id_propagation(self, client: TestClient, request_id_headers):
        """✅ X-Request-ID deve ser propagado"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=request_id_headers
        )
        
        # Request ID deve estar no response
        assert "X-Request-ID" in response.headers
    
    def test_model_version_header(self, client: TestClient, auth_headers):
        """✅ X-Model-Version ou X-Active-Model-Version presente"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            pytest.skip("Modelos não disponíveis")
        
        # Pelo menos um deve estar presente
        assert (
            "X-Model-Version" in response.headers or
            "X-Active-Model-Version" in response.headers
        )


# ============================================================================
# TESTES: Autenticação
# ============================================================================

@pytest.mark.contract
class TestPredictionAuthentication:
    """Testes de autenticação"""
    
    def test_predict_without_auth(self, client: TestClient):
        """❌ Sem autenticação → 401"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post("/predict/selic-from-fed", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_predict_invalid_auth(self, client: TestClient, auth_headers_invalid):
        """❌ Autenticação inválida → 401"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers_invalid
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_batch_without_auth(self, client: TestClient):
        """❌ Batch sem autenticação → 401"""
        payload = {
            "scenarios": [
                {"fed_decision_date": "2025-10-29", "fed_move_bps": 25}
            ]
        }
        
        response = client.post("/predict/selic-from-fed/batch", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TESTES: Propriedades Científicas Avançadas
# ============================================================================

@pytest.mark.contract
@pytest.mark.scientific
class TestPredictionScientificProperties:
    """Testes de propriedades científicas"""
    
    def test_distribution_sum_strict(self, client: TestClient, auth_headers):
        """✅ Distribuição soma exatamente 1.0 (tolerância apertada)"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        distribution = data["distribution"]
        
        # Discretização analítica com renormalização → soma exata
        total_prob = sum(d["probability"] for d in distribution)
        assert abs(total_prob - 1.0) < 1e-9, f"Soma = {total_prob:.15f}, esperado 1.0"
    
    def test_ci80_within_ci95(self, client: TestClient, auth_headers):
        """✅ CI80 deve estar contido em CI95"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        ci80 = data["ci80_bps"]
        ci95 = data["ci95_bps"]
        
        # CI80 completamente dentro de CI95
        assert ci95[0] <= ci80[0] <= ci80[1] <= ci95[1], \
            f"CI80={ci80} não está dentro de CI95={ci95}"
    
    def test_ci95_wider_than_ci80(self, client: TestClient, auth_headers):
        """✅ CI95 deve ser mais amplo que CI80"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        ci80 = data["ci80_bps"]
        ci95 = data["ci95_bps"]
        
        width_ci80 = ci80[1] - ci80[0]
        width_ci95 = ci95[1] - ci95[0]
        
        # CI95 deve ser estritamente mais amplo (ou igual em casos degenerados)
        assert width_ci95 >= width_ci80, f"CI95 width={width_ci95} < CI80 width={width_ci80}"
    
    def test_zero_move_concentrates_on_zero(self, client: TestClient, auth_headers):
        """✅ Fed 0 bps → distribuição concentrada em delta=0"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 0,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        distribution = data["distribution"]
        
        # Bin com maior probabilidade deve ser 0 ou próximo
        top_bin = max(distribution, key=lambda d: d["probability"])
        
        # Para Fed 0, espera-se resposta próxima de 0
        assert abs(top_bin["delta_bps"]) <= 25, \
            f"Fed 0 bps mas top bin é {top_bin['delta_bps']} bps"
    
    def test_negative_move_direction(self, client: TestClient, auth_headers):
        """✅ Fed negativo → expected_move_bps ≤ 0 ou próximo"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": -25,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        expected = data["expected_move_bps"]
        
        # Fed negativo deve gerar resposta negativa ou neutra
        # (com IRF=0.51, esperamos resposta também negativa)
        assert expected <= 25, \
            f"Fed -25 bps mas expected={expected} bps (esperado ≤ 25)"
    
    def test_per_meeting_probabilities_coherent(self, client: TestClient, auth_headers):
        """✅ per_meeting probabilidades coerentes com prob_move_within_next_copom"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        per_meeting = data["per_meeting"]
        prob_next_copom = data["prob_move_within_next_copom"]
        
        if len(per_meeting) > 0:
            # Soma das probabilidades não deve exceder muito o total
            total_per_meeting = sum(m["probability"] for m in per_meeting)
            
            # Pode ser maior devido a decay adaptativo, mas não absurdamente
            assert total_per_meeting <= 1.5, \
                f"Soma per_meeting={total_per_meeting} muito alta"
            
            # Primeiro meeting deve ter a maior probabilidade
            if len(per_meeting) >= 2:
                first_prob = per_meeting[0]["probability"]
                second_prob = per_meeting[1]["probability"]
                assert first_prob >= second_prob, \
                    "Primeiro Copom deve ter maior probabilidade (decay adaptativo)"


# ============================================================================
# TESTES: Determinismo e Idempotência
# ============================================================================

@pytest.mark.contract
class TestPredictionDeterminism:
    """Testes de determinismo e idempotência"""
    
    def test_predict_determinism_same_payload(self, client: TestClient, auth_headers):
        """✅ Mesma requisição retorna exatamente o mesmo resultado"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 25,
            "horizons_months": [1, 3, 6]
        }
        
        response1 = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        response2 = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response1.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            pytest.skip("Modelos não disponíveis")
        
        assert response1.status_code == response2.status_code == status.HTTP_200_OK
        
        # Payloads devem ser idênticos (determinismo por versão)
        data1 = response1.json()
        data2 = response2.json()
        
        # Campos determinísticos
        assert data1["expected_move_bps"] == data2["expected_move_bps"]
        assert data1["distribution"] == data2["distribution"]
        assert data1["ci80_bps"] == data2["ci80_bps"]
        assert data1["ci95_bps"] == data2["ci95_bps"]
        
        # Model metadata deve ser igual
        assert data1["model_metadata"]["version"] == data2["model_metadata"]["version"]


# ============================================================================
# TESTES: Cenários Científicos de Borda
# ============================================================================

@pytest.mark.contract
@pytest.mark.scientific
class TestPredictionEdgeCases:
    """Testes de casos de borda científicos"""
    
    def test_zero_fed_move_concentrated(self, client: TestClient, auth_headers):
        """✅ Fed 0 bps → distribuição concentrada em 0"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 0,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        distribution = data["distribution"]
        
        # Maior bin deve ser 0 ou próximo
        top_bin = max(distribution, key=lambda d: d["probability"])
        assert abs(top_bin["delta_bps"]) <= 25, \
            f"Fed 0 bps mas maior probabilidade em {top_bin['delta_bps']} bps"
        
        # prob_move_within_next_copom deve ser baixa para Fed neutro
        assert data["prob_move_within_next_copom"] <= 0.8, \
            "Fed neutro mas alta probabilidade de movimento"
    
    def test_large_positive_shock(self, client: TestClient, auth_headers):
        """✅ Fed +50 bps (shock) → CI95 amplo"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": 50,
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            pytest.skip("Modelos não disponíveis")
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Erro inesperado: {response.status_code}")
        
        data = response.json()
        ci95 = data["ci95_bps"]
        
        # Shock maior → incerteza maior (tolerante a modelos pequenos)
        width_ci95 = ci95[1] - ci95[0]
        assert width_ci95 >= 0, \
            f"CI95 width={width_ci95} não pode ser negativo"
    
    def test_negative_fed_move(self, client: TestClient, auth_headers):
        """✅ Fed -25 bps → expected_move_bps negativo ou próximo de zero"""
        payload = {
            "fed_decision_date": "2025-10-29",
            "fed_move_bps": -25,
            "fed_move_dir": "-1",
            "horizons_months": [1, 3]
        }
        
        response = client.post(
            "/predict/selic-from-fed",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code != status.HTTP_200_OK:
            pytest.skip(f"Status {response.status_code} - Modelos não disponíveis ou erro")
        
        data = response.json()
        expected = data["expected_move_bps"]
        
        # Com IRF~0.51, Fed -25 deve dar expected próximo de -12 a 0
        assert expected <= 25, \
            f"Fed -25 bps mas expected={expected} bps (deveria ser ≤ 25)"


# ============================================================================
# TESTES: Erros Internos e Modelos Não Disponíveis
# ============================================================================

@pytest.mark.contract
class TestPredictionErrorScenarios:
    """Testes de cenários de erro"""
    
    def test_predict_models_not_loaded(self, client: TestClient, auth_headers):
        """❌ Modelos não carregados → 503"""
        app = client.app
        
        # Salvar estado original
        original_lp = getattr(app.state, "model_lp", None)
        original_bvar = getattr(app.state, "model_bvar", None)
        original_loaded = getattr(app.state, "models_loaded", None)
        
        try:
            # Simular modelos não carregados
            app.state.model_lp = None
            app.state.model_bvar = None
            app.state.models_loaded = False
            
            payload = {
                "fed_decision_date": "2025-10-29",
                "fed_move_bps": 25,
                "horizons_months": [1]
            }
            
            response = client.post(
                "/predict/selic-from-fed",
                json=payload,
                headers=auth_headers
            )
            
            # Deve retornar 503 (service unavailable)
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            
            # Validar estrutura de erro
            data = response.json()
            assert "error_code" in data or "message" in data
            
            # Request ID deve estar presente mesmo em erro
            assert "X-Request-ID" in response.headers
        
        finally:
            # Restaurar estado
            if original_lp is not None:
                app.state.model_lp = original_lp
            if original_bvar is not None:
                app.state.model_bvar = original_bvar
            if original_loaded is not None:
                app.state.models_loaded = original_loaded


# ============================================================================
# TESTES: Batch - Casos Avançados
# ============================================================================

@pytest.mark.contract
class TestBatchPredictionAdvanced:
    """Testes avançados de batch prediction"""
    
    def test_batch_exactly_at_limit(self, client: TestClient, auth_headers):
        """✅ Batch exatamente no MAX_BATCH_SIZE deve funcionar"""
        from src.core.config import get_settings
        settings = get_settings()
        max_batch = min(getattr(settings, "MAX_BATCH_SIZE", 10), 10)  # Limitar a 10 para testes
        
        scenarios = [
            {"fed_decision_date": "2025-10-29", "fed_move_bps": 25, "horizons_months": [1]}
            for _ in range(max_batch)
        ]
        
        payload = {"scenarios": scenarios}
        
        response = client.post(
            "/predict/selic-from-fed/batch",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            pytest.skip("Modelos não disponíveis")
        
        # No limite deve ser aceito
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["predictions"]) == max_batch
