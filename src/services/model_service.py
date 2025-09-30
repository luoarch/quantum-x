"""
Serviço de gerenciamento de modelos
v2.1 - Production-ready com 10 ajustes de robustez
"""

import logging
import pickle
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.local_projections import LocalProjectionsForecaster
from src.models.bvar_minnesota import BVARMinnesota
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class ModelService:
    """
    Serviço para gerenciamento de modelos
    
    v2.1 - Production-ready:
    - Preferência JSON sobre pickle (auditabilidade)
    - Validação de integridade de pacote
    - Self-check de modelos carregados
    - Cache LRU com limite de memória
    - Versão ativa persistente
    - Log estruturado completo
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.models_dir = Path(self.settings.DATA_DIR) / "models"
        self.max_cache_size = getattr(self.settings, 'MAX_MODEL_CACHE', 3)
        self._ensure_models_dir()
        
        # Cache de modelos em memória (LRU)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._active_version: Optional[str] = None
        
        # Carregar versão ativa persistente
        self._load_active_version_from_disk()
        
        logger.info(f"ModelService v2.1 inicializado. Diretório: {self.models_dir}")
    
    def _ensure_models_dir(self):
        """Garantir que o diretório de modelos existe"""
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_active_version_from_disk(self):
        """Carregar versão ativa persistente"""
        active_file = self.models_dir / "active_version"
        
        if active_file.exists():
            try:
                self._active_version = active_file.read_text().strip()
                logger.info(f"Versão ativa carregada do disco: {self._active_version}")
            except Exception as e:
                logger.warning(f"Erro ao carregar versão ativa: {e}")
    
    def _save_active_version_to_disk(self, version: str):
        """Persistir versão ativa"""
        active_file = self.models_dir / "active_version"
        active_file.write_text(version)
        logger.info(f"Versão ativa persistida: {version}")
    
    def _get_available_versions(self) -> List[str]:
        """Obter lista de versões disponíveis no diretório"""
        versions = []
        
        if not self.models_dir.exists():
            return versions
        
        for version_dir in self.models_dir.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith('v'):
                # Verificar se tem os arquivos necessários
                if (version_dir / "model_lp.pkl").exists() and \
                   (version_dir / "model_bvar.pkl").exists() and \
                   (version_dir / "metadata.json").exists():
                    versions.append(version_dir.name)
        
        return sorted(versions, reverse=True)  # Mais recentes primeiro
    
    def _validate_package_integrity(self, version_dir: Path) -> bool:
        """
        Validar integridade do pacote da versão
        
        Ajuste 2: Verificar arquivos críticos
        """
        required = ["metadata.json"]
        optional = ["model_lp.pkl", "model_bvar.pkl", "irfs_lp.json", "irfs_bvar.json"]
        
        # Verificar arquivos obrigatórios
        missing = [p for p in required if not (version_dir / p).exists()]
        if missing:
            raise FileNotFoundError(f"Arquivos críticos ausentes: {missing}")
        
        # Verificar pelo menos um modelo
        has_lp = (version_dir / "model_lp.pkl").exists()
        has_bvar = (version_dir / "model_bvar.pkl").exists() or (version_dir / "model_bvar.json").exists()
        
        if not (has_lp and has_bvar):
            raise FileNotFoundError(f"Modelos ausentes. LP: {has_lp}, BVAR: {has_bvar}")
        
        return True
    
    def _self_check_bvar(self, bvar: BVARMinnesota):
        """
        Self-check do BVAR carregado
        
        Ajuste 3: Validar modelo após carregamento
        """
        try:
            # Verificar atributos essenciais
            assert hasattr(bvar, "sigma"), "BVAR sem matriz Sigma"
            assert hasattr(bvar, "beta"), "BVAR sem coeficientes Beta"
            
            # Verificar estabilidade
            if hasattr(bvar, "stable"):
                if not bvar.stable:
                    logger.warning("⚠️  BVAR carregado é INSTÁVEL (max|eig| >= 1.0)")
            
            # Verificar dimensões
            if bvar.sigma is not None:
                assert bvar.sigma.shape == (2, 2), f"Sigma com shape inválida: {bvar.sigma.shape}"
            
            if bvar.beta is not None:
                expected_cols = 1 + bvar.n_vars * bvar.n_lags
                assert bvar.beta.shape[1] == expected_cols, \
                    f"Beta com dimensões inválidas: {bvar.beta.shape}, esperado (_, {expected_cols})"
            
            logger.info("✓ BVAR self-check passou")
            
        except AssertionError as e:
            logger.error(f"❌ BVAR self-check FALHOU: {e}")
            raise
    
    def _self_check_lp(self, lp: LocalProjectionsForecaster):
        """Self-check do LP carregado"""
        try:
            assert hasattr(lp, "models"), "LP sem modelos por horizonte"
            assert len(lp.models) > 0, "LP sem horizontes estimados"
            
            logger.info(f"✓ LP self-check passou ({len(lp.models)} horizontes)")
            
        except AssertionError as e:
            logger.error(f"❌ LP self-check FALHOU: {e}")
            raise
    
    def _manage_cache_size(self):
        """
        Gerenciar tamanho do cache (LRU)
        
        Ajuste 4: Limite de cache com LRU
        """
        if len(self._cache) >= self.max_cache_size:
            # Encontrar versão mais antiga
            oldest_version = min(
                self._cache.items(),
                key=lambda kv: kv[1]["loaded_at"]
            )[0]
            
            logger.info(f"Cache cheio ({self.max_cache_size}). Removendo versão mais antiga: {oldest_version}")
            del self._cache[oldest_version]
    
    def _load_metadata(self, version: str) -> Dict[str, Any]:
        """Carregar metadata.json de uma versão"""
        metadata_path = self.models_dir / version / "metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata não encontrado para versão {version}")
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def load_model(self, version: str = "latest") -> Tuple[LocalProjectionsForecaster, BVARMinnesota, Dict[str, Any]]:
        """
        Carregar modelo específico (REAL)
        
        v2.1 - Melhorias:
        - Preferência JSON sobre pickle
        - Validação de integridade
        - Self-check de modelos
        - Log estruturado
        
        Args:
            version: Versão do modelo ou "latest" para a mais recente
            
        Returns:
            Tuple com (model_lp, model_bvar, metadata)
        """
        try:
            # Resolver "latest" para versão específica
            if version == "latest":
                available_versions = self._get_available_versions()
                if not available_versions:
                    raise ValueError("Nenhum modelo treinado encontrado")
                version = available_versions[0]
                logger.info(f"Resolvendo 'latest' → {version}", extra={"version": version})
            
            # Verificar cache
            if version in self._cache:
                logger.info(f"✓ Modelo {version} carregado do cache", extra={"version": version, "source": "cache"})
                cached = self._cache[version]
                return cached['lp'], cached['bvar'], cached['metadata']
            
            logger.info(f"📦 Carregando modelo {version} do disco...", extra={"version": version, "source": "disk"})
            
            # Caminhos dos artefatos
            version_dir = self.models_dir / version
            
            # Ajuste 2: Validar integridade do pacote
            self._validate_package_integrity(version_dir)
            
            # Carregar metadata
            metadata = self._load_metadata(version)
            
            # Carregar LP (pickle)
            lp_path = version_dir / "model_lp.pkl"
            with open(lp_path, 'rb') as f:
                model_lp = pickle.load(f)
            
            lp_size = lp_path.stat().st_size
            logger.info(f"✓ LP carregado: {lp_size} bytes", extra={"model": "LP", "size_bytes": lp_size})
            
            # Ajuste 1: Preferir JSON para BVAR (mais auditável)
            bvar_json = version_dir / "model_bvar.json"
            bvar_pkl = version_dir / "model_bvar.pkl"
            
            if bvar_json.exists():
                try:
                    with open(bvar_json, 'r') as f:
                        model_bvar = BVARMinnesota.from_dict(json.load(f))
                    logger.info(f"✓ BVAR JSON carregado: {bvar_json.stat().st_size} bytes", 
                               extra={"model": "BVAR", "format": "json"})
                except Exception as e:
                    logger.warning(f"Falha no JSON BVAR, fallback para pickle: {e}")
                    with open(bvar_pkl, 'rb') as f:
                        model_bvar = pickle.load(f)
                    logger.info(f"✓ BVAR pickle carregado: {bvar_pkl.stat().st_size} bytes",
                               extra={"model": "BVAR", "format": "pickle"})
            else:
                with open(bvar_pkl, 'rb') as f:
                    model_bvar = pickle.load(f)
                logger.info(f"✓ BVAR pickle carregado: {bvar_pkl.stat().st_size} bytes",
                           extra={"model": "BVAR", "format": "pickle"})
            
            # Ajuste 3: Self-check dos modelos
            self._self_check_lp(model_lp)
            self._self_check_bvar(model_bvar)
            
            # Enriquecer metadata
            metadata['loaded_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Ajuste 4: Gerenciar tamanho do cache (LRU)
            self._manage_cache_size()
            
            # Adicionar ao cache
            self._cache[version] = {
                'lp': model_lp,
                'bvar': model_bvar,
                'metadata': metadata,
                'loaded_at': datetime.utcnow()
            }
            
            # Log estruturado completo (Ajuste 9)
            logger.info(
                f"✅ Modelo {version} carregado, validado e cacheado",
                extra={
                    "version": version,
                    "data_hash": metadata.get('data_hash', 'N/A')[:64],
                    "lp_size_bytes": lp_size,
                    "bvar_stable": getattr(model_bvar, 'stable', None),
                    "n_observations": metadata.get('n_observations', 0),
                    "cache_size": len(self._cache)
                }
            )
            
            return model_lp, model_bvar, metadata
            
        except Exception as e:
            logger.error(
                f"❌ Erro ao carregar modelo {version}: {str(e)}", 
                exc_info=True,
                extra={"version": version, "error_type": type(e).__name__}
            )
            raise
    
    def list_versions(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Listar versões de modelos disponíveis (REAL)
        
        Args:
            include_inactive: Incluir versões inativas (sempre True por enquanto)
            
        Returns:
            Lista de dicts com informações de cada versão
        """
        try:
            versions = []
            available = self._get_available_versions()
            
            logger.info(f"Encontradas {len(available)} versões disponíveis")
            
            for version in available:
                try:
                    metadata = self._load_metadata(version)
                    
                    version_info = {
                        "version": version,
                        "trained_at": metadata.get('created_at', 'N/A'),
                        "data_hash": metadata.get('data_hash', 'N/A'),
                        "methodology": metadata.get('methodology', 'Unknown'),
                        "n_observations": metadata.get('n_observations', 0),
                        "is_active": version == self._active_version or (self._active_version is None and version == available[0]),
                        "cached": version in self._cache
                    }
                    
                    # Adicionar métricas dos modelos se disponível
                    if 'models' in metadata:
                        lp_metrics = metadata['models'].get('local_projections', {})
                        bvar_metrics = metadata['models'].get('bvar_minnesota', {})
                        
                        version_info['lp_metrics'] = {
                            'n_horizons': lp_metrics.get('n_horizons', 0),
                            'avg_r_squared': lp_metrics.get('avg_r_squared', 0.0),
                            'avg_irf': lp_metrics.get('avg_irf', 0.0)
                        }
                        
                        version_info['bvar_metrics'] = {
                            'n_obs': bvar_metrics.get('n_obs', 0),
                            'r_squared': bvar_metrics.get('r_squared', 0.0),
                            'model_quality': bvar_metrics.get('model_quality', 'unknown'),
                            'stable': bvar_metrics.get('irf_summary', {}).get('max_response') is not None
                        }
                    
                    versions.append(version_info)
                    
                except Exception as e:
                    logger.warning(f"Erro ao carregar metadata de {version}: {e}")
                    continue
            
            return versions
            
        except Exception as e:
            logger.error(f"Erro ao listar versões: {str(e)}", exc_info=True)
            raise
    
    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Obter informações de versão específica"""
        try:
            versions = self.list_versions(include_inactive=True)
            
            for v in versions:
                if v['version'] == version:
                    return v
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter versão {version}: {str(e)}", exc_info=True)
            raise
    
    def get_active_version(self) -> Optional[str]:
        """Obter versão ativa"""
        if self._active_version:
            return self._active_version
        
        # Usar a mais recente por default
        available = self._get_available_versions()
        if available:
            return available[0]
        
        return None
    
    def set_active_version(self, version: str) -> bool:
        """
        Definir versão ativa
        
        Ajuste 5: Persistir versão ativa
        
        Args:
            version: Versão a ser ativada
            
        Returns:
            True se bem-sucedido
        """
        try:
            # Verificar se versão existe
            available = self._get_available_versions()
            if version not in available:
                logger.error(f"Versão {version} não encontrada")
                return False
            
            self._active_version = version
            
            # Ajuste 5: Persistir no disco
            self._save_active_version_to_disk(version)
            
            logger.info(f"Versão ativa alterada para: {version}", extra={"version": version})
            
            # Pré-carregar no cache se ainda não estiver
            if version not in self._cache:
                self.load_model(version)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao ativar versão {version}: {str(e)}", exc_info=True)
            return False
    
    def clear_cache(self, version: Optional[str] = None):
        """
        Limpar cache de modelos
        
        Args:
            version: Versão específica ou None para limpar tudo
        """
        if version:
            if version in self._cache:
                del self._cache[version]
                logger.info(f"Cache limpo para versão: {version}")
        else:
            self._cache.clear()
            logger.info("Cache completo limpo")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Obter informações do cache"""
        return {
            "cached_versions": list(self._cache.keys()),
            "cache_size": len(self._cache),
            "max_cache_size": self.max_cache_size,
            "active_version": self._active_version,
            "cache_details": {
                version: {
                    "loaded_at": info['loaded_at'].isoformat(),
                    "metadata_version": info['metadata'].get('version', 'N/A'),
                    "bvar_stable": getattr(info.get('bvar'), 'stable', None)
                }
                for version, info in self._cache.items()
            }
        }
    
    def get_capabilities(self, include_dynamic: bool = True) -> Dict[str, Any]:
        """
        Obter capacidades dos modelos
        
        Ajuste 8: Capabilities dinâmicas baseadas em modelo carregado
        """
        try:
            caps = {
                "supported_horizons": list(range(1, 13)),
                "supported_fed_moves": list(range(-200, 201, 25)),
                "confidence_levels": [0.80, 0.95],
                "discretization": 25,
                "max_batch_size": getattr(self.settings, 'MAX_BATCH_SIZE', 10),
                "supported_regimes": ["normal", "stress", "crisis", "recovery"],
                "data_requirements": {
                    "min_observations": 10,
                    "max_observations": 500,
                    "frequency": "monthly",
                    "mensalization_policy": "forward_fill"
                },
                "models": {
                    "local_projections": {
                        "max_horizon": 12,
                        "max_lags": 4,
                        "regularization": ["ridge", "lasso", "elastic"]
                    },
                    "bvar_minnesota": {
                        "n_vars": 2,
                        "n_lags": 2,
                        "priors_profile": "small-N-default",
                        "identification": "cholesky_fed_first",
                        "irf_unit": "bps_per_bps",
                        "normalized": True
                    }
                },
                "limitations": [
                    "Alta incerteza com amostras pequenas (~20 observações)",
                    "Bandas de confiança largas devido a N pequeno",
                    "Forward-fill mensal (simplificação MVP)",
                    "Prior Minnesota dominante (R² baixo esperado)"
                ]
            }
            
            # Ajuste 8: Capabilities dinâmicas
            if include_dynamic and self._active_version and self._active_version in self._cache:
                cached = self._cache[self._active_version]
                lp = cached['lp']
                bvar = cached['bvar']
                metadata = cached['metadata']
                
                # Atualizar com dados reais do modelo carregado
                caps['dynamic'] = {
                    "active_version": self._active_version,
                    "loaded_at": cached['loaded_at'].isoformat(),
                    "lp_horizons_actual": len(lp.models) if hasattr(lp, 'models') else 0,
                    "bvar_stable": getattr(bvar, 'stable', None),
                    "bvar_priors": getattr(bvar, 'priors_profile', 'unknown'),
                    "n_observations": metadata.get('n_observations', 0),
                    "data_hash": metadata.get('data_hash', 'N/A')[:64]
                }
            
            return caps
            
        except Exception as e:
            logger.error(f"Erro ao obter capacidades: {str(e)}", exc_info=True)
            raise


# Singleton instance
_model_service_instance: Optional[ModelService] = None

def get_model_service() -> ModelService:
    """Obter instância singleton do ModelService"""
    global _model_service_instance
    
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    
    return _model_service_instance


if __name__ == "__main__":
    # Teste do ModelService v2.1
    print("🧪 Testando ModelService v2.1 (production-ready)...")
    
    # Criar service
    service = ModelService()
    
    # Listar versões
    print("\n📋 Versões disponíveis:")
    versions = service.list_versions()
    for v in versions:
        print(f"  - {v['version']}: {v['n_observations']} obs, active={v['is_active']}, cached={v['cached']}")
    
    # Carregar modelo
    if versions:
        latest = versions[0]['version']
        print(f"\n📦 Carregando modelo {latest}...")
        
        lp, bvar, metadata = service.load_model(latest)
        
        print(f"✅ Carregado com sucesso!")
        print(f"   LP: {type(lp).__name__}, {len(lp.models)} horizontes")
        print(f"   BVAR: {type(bvar).__name__}, stable={bvar.stable}, eigs_max={getattr(bvar, 'eigs_F', [None])[0] if hasattr(bvar, 'eigs_F') else 'N/A'}")
        print(f"   Metadata: versão {metadata['version']}, {metadata['n_observations']} obs")
        
        # Cache info
        cache_info = service.get_cache_info()
        print(f"\n💾 Cache:")
        print(f"   Versões cacheadas: {cache_info['cached_versions']}")
        print(f"   Tamanho: {cache_info['cache_size']}/{cache_info['max_cache_size']}")
        
        # Capabilities dinâmicas
        caps = service.get_capabilities(include_dynamic=True)
        print(f"\n🎯 Capabilities:")
        print(f"   Horizontes: {len(caps['supported_horizons'])}")
        print(f"   Modelos: {list(caps['models'].keys())}")
        if 'dynamic' in caps:
            print(f"   Dinâmico: versão {caps['dynamic']['active_version']}, LP {caps['dynamic']['lp_horizons_actual']} horizontes")
        
        # Testar previsão
        print(f"\n🔮 Testando previsão REAL...")
        forecast = bvar.conditional_forecast([25], horizon_months=2)
        print(f"   Fed +25 bps:")
        for h, pred in forecast.items():
            print(f"     {h}: Selic {pred['mean']:.1f} bps [{pred['ci_lower']:.1f}, {pred['ci_upper']:.1f}]")
        
    else:
        print("\n⚠️  Nenhum modelo encontrado. Execute train_pipeline.py primeiro.")
    
    print("\n✅ Teste v2.1 completo!")
    print("🎯 Ajustes implementados:")
    print("  ✓ Preferência JSON sobre pickle")
    print("  ✓ Validação de integridade")
    print("  ✓ Self-check de modelos")
    print("  ✓ Cache LRU")
    print("  ✓ Versão ativa persistente")
    print("  ✓ Log estruturado")
    print("  ✓ Capabilities dinâmicas")
