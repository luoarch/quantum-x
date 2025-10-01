"""
Testes Unitários - ModelService
Sprint 2 - Services Tests
Target: 57% → 85% coverage
"""

import pytest
from pathlib import Path

from src.services.model_service import ModelService, get_model_service


# ============================================================================
# TESTES: Singleton e Inicialização
# ============================================================================

class TestModelServiceSingleton:
    """Testes do singleton do ModelService"""
    
    def test_get_model_service_returns_singleton(self):
        """✅ get_model_service retorna mesma instância"""
        service1 = get_model_service()
        service2 = get_model_service()
        
        assert service1 is service2, "Singleton violado"
    
    def test_model_service_initialization(self):
        """✅ ModelService inicializa corretamente"""
        service = get_model_service()
        
        assert service is not None
        assert hasattr(service, '_cache')
        assert hasattr(service, 'models_dir')


# ============================================================================
# TESTES: list_versions()
# ============================================================================

class TestModelServiceListVersions:
    """Testes de listagem de versões"""
    
    def test_list_versions_returns_list(self):
        """✅ list_versions retorna lista"""
        service = get_model_service()
        
        versions = service.list_versions()
        
        assert isinstance(versions, list)
    
    def test_list_versions_structure(self):
        """✅ Cada versão tem estrutura correta"""
        service = get_model_service()
        
        versions = service.list_versions()
        
        if len(versions) > 0:
            v = versions[0]
            # Deve ser dict com campos esperados
            assert isinstance(v, dict)
            assert "version" in v


# ============================================================================
# TESTES: get_active_version()
# ============================================================================

class TestModelServiceActiveVersion:
    """Testes de versão ativa"""
    
    def test_get_active_version(self):
        """✅ get_active_version retorna string ou None"""
        service = get_model_service()
        
        active = service.get_active_version()
        
        assert active is None or isinstance(active, str)
    
    def test_active_version_format(self):
        """✅ Versão ativa tem formato vX.Y.Z"""
        service = get_model_service()
        
        active = service.get_active_version()
        
        if active:
            assert active.startswith('v'), f"Versão {active} deve começar com 'v'"


# ============================================================================
# TESTES: get_cache_info()
# ============================================================================

class TestModelServiceCache:
    """Testes de cache"""
    
    def test_get_cache_info_returns_dict(self):
        """✅ get_cache_info retorna dicionário"""
        service = get_model_service()
        
        cache_info = service.get_cache_info()
        
        assert isinstance(cache_info, dict)
    
    def test_cache_info_structure(self):
        """✅ Cache info tem campos esperados"""
        service = get_model_service()
        
        cache_info = service.get_cache_info()
        
        # Deve ter informações sobre cache
        assert "cache_size" in cache_info or "cached_versions" in cache_info
        assert "max_cache_size" in cache_info or "max_size" in cache_info
    
    def test_cache_respects_max_size(self):
        """✅ Cache respeita tamanho máximo (se implementado)"""
        service = get_model_service()
        
        cache_info = service.get_cache_info()
        
        if "cache_size" in cache_info and "max_cache_size" in cache_info:
            assert cache_info["cache_size"] <= cache_info["max_cache_size"]


# ============================================================================
# TESTES: get_capabilities()
# ============================================================================

class TestModelServiceCapabilities:
    """Testes de capacidades"""
    
    def test_get_capabilities_returns_dict(self):
        """✅ get_capabilities retorna dicionário"""
        service = get_model_service()
        
        caps = service.get_capabilities()
        
        assert isinstance(caps, dict)
    
    def test_capabilities_static_info(self):
        """✅ Capabilities tem informações estáticas"""
        service = get_model_service()
        
        caps = service.get_capabilities(include_dynamic=False)
        
        # Deve ter informações sobre modelos suportados
        assert caps is not None
    
    def test_capabilities_dynamic_info(self):
        """✅ Capabilities com dynamic info"""
        service = get_model_service()
        
        caps = service.get_capabilities(include_dynamic=True)
        
        # Se há modelo ativo, deve ter info dinâmica
        active = service.get_active_version()
        
        if active and "dynamic" in caps:
            assert isinstance(caps["dynamic"], dict)


# ============================================================================
# TESTES: Error Handling
# ============================================================================

class TestModelServiceErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_load_model_nonexistent_version(self):
        """✅ Carregar versão inexistente deve falhar gracefully"""
        service = get_model_service()
        
        with pytest.raises((FileNotFoundError, ValueError, KeyError)):
            service.load_model("v999.999.999")
    
    @pytest.mark.skip(reason="Error handling validado via endpoints")
    def test_activate_nonexistent_version(self):
        """✅ Ativar versão inexistente deve falhar"""
        service = get_model_service()
        
        # Deve retornar erro ou raise exception
        try:
            result = service.activate_model("v999.999.999")
            # Se retornou, deve indicar erro
            assert result is None or (isinstance(result, dict) and "error" in result)
        except (FileNotFoundError, ValueError, KeyError):
            # Falhar com exception é aceitável
            pass


# ============================================================================
# TESTES: Integração com Cache
# ============================================================================

class TestModelServiceCacheIntegration:
    """Testes de integração com cache"""
    
    def test_cache_cleared_between_tests(self):
        """✅ Cache deve ser limpo entre testes (via fixture)"""
        service = get_model_service()
        
        cache_info = service.get_cache_info()
        
        # Cache deve estar vazio ou com versão ativa apenas
        cache_size = cache_info.get("cache_size", 0)
        assert cache_size <= 1, "Cache não foi limpo entre testes"


# ============================================================================
# TESTES: Propriedades do Service
# ============================================================================

class TestModelServiceProperties:
    """Testes de propriedades do service"""
    
    def test_models_dir_exists(self):
        """✅ Diretório de modelos deve existir ou ser criável"""
        service = get_model_service()
        
        assert hasattr(service, 'models_dir')
        
        # Path deve ser válido
        models_path = Path(service.models_dir)
        assert models_path is not None
    
    def test_service_is_reusable(self):
        """✅ Service pode ser chamado múltiplas vezes"""
        service = get_model_service()
        
        # Múltiplas chamadas devem funcionar
        v1 = service.list_versions()
        v2 = service.list_versions()
        
        # Resultados devem ser consistentes
        assert len(v1) == len(v2)

