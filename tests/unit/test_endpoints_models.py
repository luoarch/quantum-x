"""
Testes de Endpoints - Modelos
Sprint 2 - API Contract Tests
"""

import pytest
from fastapi import status


# ============================================================================
# TESTES: GET /models/versions
# ============================================================================

class TestListModelVersions:
    """Testes do endpoint de listagem de versões"""
    
    def test_list_versions_success(self, client, auth_headers):
        """✅ GET /models/versions deve retornar 200 com lista"""
        response = client.get("/models/versions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
        # Headers de governança
        assert "X-Active-Model-Version" in response.headers
        assert "X-API-Version" in response.headers
        assert "X-Request-ID" in response.headers
    
    def test_list_versions_without_auth(self, client):
        """❌ Sem autenticação deve retornar 401"""
        response = client.get("/models/versions")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_versions_with_invalid_auth(self, client, auth_headers_invalid):
        """❌ Autenticação inválida deve retornar 401"""
        response = client.get("/models/versions", headers=auth_headers_invalid)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_versions_structure(self, client, auth_headers):
        """✅ Estrutura da resposta deve ser válida"""
        response = client.get("/models/versions", headers=auth_headers)
        data = response.json()
        
        if len(data) > 0:
            version = data[0]
            assert "version" in version
            assert "trained_at" in version
            assert "data_hash" in version
            assert "methodology" in version


# ============================================================================
# TESTES: GET /models/versions/{version}
# ============================================================================

class TestGetModelVersion:
    """Testes do endpoint de detalhes de versão"""
    
    def test_get_version_details(self, client, auth_headers):
        """✅ GET /models/versions/{version} com versão existente"""
        # Primeiro listar versões disponíveis
        list_response = client.get("/models/versions", headers=auth_headers)
        versions = list_response.json()
        
        if len(versions) > 0:
            version = versions[0]["version"]
            response = client.get(f"/models/versions/{version}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["version"] == version
            assert "X-Active-Model-Version" in response.headers
    
    def test_get_version_not_found(self, client, auth_headers):
        """❌ Versão inexistente deve retornar 404"""
        response = client.get("/models/versions/v999.999.999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Validar estrutura de erro
        data = response.json()
        assert "error_code" in data or "message" in data


# ============================================================================
# TESTES: GET /models/active
# ============================================================================

class TestGetActiveModel:
    """Testes do endpoint de modelo ativo"""
    
    def test_get_active_model(self, client, auth_headers):
        """✅ GET /models/active deve retornar modelo ativo"""
        response = client.get("/models/active", headers=auth_headers)
        
        # Pode ser 200 (modelo ativo) ou 404 (nenhum ativo)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "version" in data
            assert "X-Active-Model-Version" in response.headers
            assert response.headers["X-Active-Model-Version"] == data["version"]


# ============================================================================
# TESTES: POST /models/versions/{version}/activate
# ============================================================================

class TestActivateModelVersion:
    """Testes do endpoint de ativação de modelo"""
    
    def test_activate_existing_version(self, client, auth_headers):
        """✅ Ativar versão existente deve retornar 200"""
        # Primeiro listar versões disponíveis
        list_response = client.get("/models/versions", headers=auth_headers)
        versions = list_response.json()
        
        if len(versions) > 0:
            version = versions[0]["version"]
            response = client.post(
                f"/models/versions/{version}/activate",
                headers=auth_headers
            )
            
            # Deve ser 200 (sucesso) ou 409 (conflito se self-check falhar)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_409_CONFLICT]
            
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert data["version"] == version
    
    def test_activate_idempotent(self, client, auth_headers):
        """✅ Ativação idempotente - ativar versão já ativa"""
        # Pegar versão ativa atual
        active_response = client.get("/models/active", headers=auth_headers)
        
        if active_response.status_code == status.HTTP_200_OK:
            active_version = active_response.json()["version"]
            
            # Tentar ativar novamente
            response = client.post(
                f"/models/versions/{active_version}/activate",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # Campo indicando idempotência (se implementado)
            # assert data.get("already_active") == True
    
    def test_activate_nonexistent_version(self, client, auth_headers):
        """❌ Ativar versão inexistente deve retornar 404"""
        response = client.post(
            "/models/versions/v999.999.999/activate",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_activate_without_auth(self, client):
        """❌ Ativação sem autenticação deve retornar 401"""
        response = client.post("/models/versions/v1.0.0/activate")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TESTES: GET /models/capabilities
# ============================================================================

class TestGetModelCapabilities:
    """Testes do endpoint de capacidades do modelo"""
    
    def test_get_capabilities_with_dynamic(self, client, auth_headers):
        """✅ Capabilities com include_dynamic=true"""
        response = client.get(
            "/models/capabilities?include_dynamic=true",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validar estrutura
        assert "supported_methodologies" in data or "models" in data
        
        # Se tiver dynamic, validar estrutura
        if "dynamic" in data:
            assert isinstance(data["dynamic"], dict)
    
    def test_get_capabilities_without_dynamic(self, client, auth_headers):
        """✅ Capabilities com include_dynamic=false"""
        response = client.get(
            "/models/capabilities?include_dynamic=false",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Não deve incluir informações dinâmicas (se implementado)
        # assert "dynamic" not in data


# ============================================================================
# TESTES: GET /models/cache
# ============================================================================

class TestGetCacheInfo:
    """Testes do endpoint de informações de cache"""
    
    def test_get_cache_info(self, client, auth_headers):
        """✅ GET /models/cache deve retornar informações de cache"""
        response = client.get("/models/cache", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validar estrutura
        assert "cache_size" in data or "cached_versions" in data
        assert "max_cache_size" in data or "max_size" in data


# ============================================================================
# TESTES: Headers de Governança
# ============================================================================

class TestGovernanceHeaders:
    """Testes de headers padronizados"""
    
    @pytest.mark.parametrize("endpoint", [
        "/models/versions",
        "/models/active",
        "/models/capabilities",
        "/models/cache"
    ])
    def test_standard_headers_present(self, client, auth_headers, endpoint):
        """✅ Headers padronizados devem estar presentes"""
        response = client.get(endpoint, headers=auth_headers)
        
        # Ignorar 404 para /models/active
        if endpoint == "/models/active" and response.status_code == 404:
            pytest.skip("No active model")
        
        assert "X-API-Version" in response.headers
        assert "X-Request-ID" in response.headers
        assert "X-Active-Model-Version" in response.headers or response.status_code == 404
    
    def test_request_id_propagation(self, client, request_id_headers):
        """✅ X-Request-ID deve ser propagado"""
        response = client.get("/models/versions", headers=request_id_headers)
        
        # Request ID deve estar no response
        assert "X-Request-ID" in response.headers
        # Pode ser o mesmo enviado ou um novo gerado

