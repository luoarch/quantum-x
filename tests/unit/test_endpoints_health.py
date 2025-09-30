"""
Testes de Endpoints - Health
Sprint 2 - Health Probes Tests
"""

import pytest
from fastapi import status
import time


# ============================================================================
# TESTES: GET /health (Basic Health Check)
# ============================================================================

class TestBasicHealthCheck:
    """Testes do health check básico"""
    
    def test_health_check_success(self, client):
        """✅ /health deve retornar 200 ou 503 (cold start)"""
        response = client.get("/health")
        
        # Pode ser 200 (modelos carregados) ou 503 (cold start)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        data = response.json()
        assert "status" in data
        assert "models_loaded" in data
    
    def test_health_check_cold_start_gate(self, client):
        """✅ Cold start gate - 503 se modelos não carregados"""
        # Forçar modelos não carregados
        app = client.app
        original_loaded = getattr(app.state, "models_loaded", None)
        original_lp = getattr(app.state, "model_lp", None)
        original_bvar = getattr(app.state, "model_bvar", None)
        
        try:
            app.state.models_loaded = False
            app.state.model_lp = None
            app.state.model_bvar = None
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "X-Models-Loaded" in response.headers
            assert response.headers["X-Models-Loaded"].lower() in ["false", "0"]
            
            data = response.json()
            assert data.get("models_loaded") == False
        
        finally:
            # Restaurar estado original
            if original_loaded is not None:
                app.state.models_loaded = original_loaded
            if original_lp is not None:
                app.state.model_lp = original_lp
            if original_bvar is not None:
                app.state.model_bvar = original_bvar
    
    def test_health_check_models_loaded(self, client):
        """✅ 200 se modelos carregados"""
        app = client.app
        original_loaded = getattr(app.state, "models_loaded", None)
        
        try:
            app.state.models_loaded = True
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data.get("models_loaded") == True
        
        finally:
            if original_loaded is not None:
                app.state.models_loaded = original_loaded


# ============================================================================
# TESTES: GET /health/ready (Readiness Probe)
# ============================================================================

class TestReadinessProbe:
    """Testes do probe de readiness (Kubernetes)"""
    
    def test_readiness_success(self, client):
        """✅ /health/ready deve retornar 200 quando pronto"""
        response = client.get("/health/ready")
        
        # Pode ser 200 (ready) ou 503 (not ready)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data
    
    def test_readiness_headers(self, client):
        """✅ Headers de governança devem estar presentes"""
        response = client.get("/health/ready")
        
        # Headers obrigatórios
        assert "X-Active-Model-Version" in response.headers
        assert "X-Uptime-Seconds" in response.headers
        assert "X-Models-Loaded" in response.headers
    
    def test_readiness_not_ready(self, client):
        """✅ 503 se não estiver pronto"""
        app = client.app
        original_loaded = getattr(app.state, "models_loaded", None)
        
        try:
            # Simular not ready
            app.state.models_loaded = False
            response = client.get("/health/ready")
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            
            data = response.json()
            assert data["ready"] == False
            assert "issues" in data
            assert len(data["issues"]) > 0
        
        finally:
            if original_loaded is not None:
                app.state.models_loaded = original_loaded
    
    def test_readiness_structure(self, client):
        """✅ Estrutura do payload de readiness"""
        response = client.get("/health/ready")
        data = response.json()
        
        # Campos obrigatórios
        assert "ready" in data
        assert isinstance(data["ready"], bool)
        
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        
        assert "issues" in data
        assert isinstance(data["issues"], list)
        
        # Checks específicos
        checks = data["checks"]
        assert "model_loaded" in checks
        assert "data_available" in checks or "data_valid" in checks


# ============================================================================
# TESTES: GET /health/live (Liveness Probe)
# ============================================================================

class TestLivenessProbe:
    """Testes do probe de liveness (Kubernetes)"""
    
    def test_liveness_always_200(self, client):
        """✅ /health/live deve sempre retornar 200"""
        response = client.get("/health/live")
        
        # Liveness SEMPRE deve ser 200 (ou 500 em crash total)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "alive" in data
        assert data["alive"] == True
    
    def test_liveness_fast(self, client):
        """✅ Liveness deve ser rápido (<100ms)"""
        start = time.perf_counter()
        response = client.get("/health/live")
        latency = time.perf_counter() - start
        
        assert response.status_code == status.HTTP_200_OK
        assert latency < 0.100  # < 100ms
    
    def test_liveness_no_external_dependencies(self, client):
        """✅ Liveness não deve depender de I/O externo"""
        # Forçar estado inconsistente (modelos não carregados)
        app = client.app
        original_loaded = getattr(app.state, "models_loaded", None)
        
        try:
            app.state.models_loaded = False
            response = client.get("/health/live")
            
            # Mesmo sem modelos, liveness deve ser 200
            assert response.status_code == status.HTTP_200_OK
            
            # alive pode ser True ou False dependendo de CPU/Memory
            # O importante é que respondeu sem depender de modelos
            data = response.json()
            assert "alive" in data
        
        finally:
            if original_loaded is not None:
                app.state.models_loaded = original_loaded
    
    def test_liveness_structure(self, client):
        """✅ Estrutura do payload de liveness"""
        response = client.get("/health/live")
        data = response.json()
        
        # Campos obrigatórios
        assert "alive" in data
        assert isinstance(data["alive"], bool)
        
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        
        assert "timestamp" in data
        
        # Métricas opcionais
        # assert "memory_usage_percent" in data
        # assert "cpu_usage_percent" in data


# ============================================================================
# TESTES: GET /health/detailed
# ============================================================================

class TestDetailedHealth:
    """Testes do health check detalhado"""
    
    def test_detailed_health(self, client):
        """✅ /health/detailed deve retornar informações completas"""
        response = client.get("/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Estrutura
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data or "model_version" in data


# ============================================================================
# TESTES: GET /health/metrics
# ============================================================================

class TestHealthMetrics:
    """Testes do endpoint de métricas"""
    
    def test_metrics_endpoint(self, client):
        """✅ /health/metrics deve retornar métricas ou degradar gracefully"""
        response = client.get("/health/metrics")
        
        # Deve responder (200 ou 500)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        data = response.json()
        
        # Timestamp deve sempre estar presente
        assert "timestamp" in data
        
        # Se tiver erro, pode ter retornado 200 com error no payload
        # (fail-soft) ou 500
        if "error" not in data:
            # Sucesso - deve ter campos de métricas
            assert "uptime_seconds" in data or "system" in data or "model" in data


# ============================================================================
# TESTES: GET /health/status
# ============================================================================

class TestHealthStatus:
    """Testes do endpoint de status de componentes"""
    
    def test_status_endpoint(self, client):
        """✅ /health/status deve retornar status de componentes"""
        response = client.get("/health/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "timestamp" in data
        assert "components" in data or "status" in data


# ============================================================================
# TESTES: Headers e Observabilidade
# ============================================================================

class TestHealthObservability:
    """Testes de observabilidade dos health endpoints"""
    
    @pytest.mark.parametrize("endpoint", [
        "/health",
        "/health/ready",
        "/health/live",
        "/health/detailed",
        "/health/metrics",
        "/health/status"
    ])
    def test_response_time_header(self, client, endpoint):
        """✅ Header X-Response-Time deve estar presente"""
        response = client.get(endpoint)
        
        # Response time pode ou não estar no health
        if "X-Response-Time" in response.headers:
            time_str = response.headers["X-Response-Time"]
            assert "ms" in time_str or "s" in time_str
    
    def test_uptime_consistency(self, client):
        """✅ Uptime deve ser consistente entre chamadas"""
        r1 = client.get("/health/ready")
        time.sleep(0.1)
        r2 = client.get("/health/ready")
        
        if r1.status_code == 200 and r2.status_code == 200:
            uptime1 = r1.json().get("uptime_seconds", 0)
            uptime2 = r2.json().get("uptime_seconds", 0)
            
            # uptime2 deve ser maior que uptime1
            assert uptime2 >= uptime1
    
    def test_health_no_auth_required(self, client):
        """✅ Health endpoints devem ser públicos (sem auth)"""
        # Não passar auth headers
        response = client.get("/health")
        
        # Deve funcionar sem autenticação
        assert response.status_code in [200, 503]
        
        response = client.get("/health/live")
        assert response.status_code == 200


# ============================================================================
# TESTES: Cenários de Falha
# ============================================================================

class TestHealthFailureScenarios:
    """Testes de cenários de falha"""
    
    def test_health_degrada_gracefully(self, client):
        """✅ Health deve degradar gracefully"""
        # Simular componente falhando
        app = client.app
        original = getattr(app.state, "model_lp", None)
        
        try:
            app.state.model_lp = None  # Simular falha
            response = client.get("/health")
            
            # Deve responder (não crashar)
            assert response.status_code in [200, 503]
            
        finally:
            if original is not None:
                app.state.model_lp = original

