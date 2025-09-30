"""
Serviço de gerenciamento de modelos
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json

from ..api.schemas import ModelVersion
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class ModelService:
    """Serviço para gerenciamento de modelos"""
    
    def __init__(self):
        self.settings = get_settings()
        self.models_dir = os.path.join(self.settings.DATA_DIR, "models")
        self._ensure_models_dir()
    
    def _ensure_models_dir(self):
        """Garantir que o diretório de modelos existe"""
        os.makedirs(self.models_dir, exist_ok=True)
    
    async def list_versions(self, include_inactive: bool = False) -> List[ModelVersion]:
        """Listar versões de modelos"""
        try:
            versions = []
            
            # Simular versões (placeholder)
            mock_versions = [
                {
                    "version": "v1.0.0",
                    "trained_at": "2025-01-01T00:00:00Z",
                    "data_hash": "sha256:abcd1234",
                    "methodology": "LP primary, BVAR fallback",
                    "n_observations": 20,
                    "r_squared": 0.65,
                    "is_active": True,
                    "backtest_metrics": {
                        "coverage_80": 0.85,
                        "coverage_95": 0.92,
                        "brier_score": 0.15
                    }
                },
                {
                    "version": "v0.9.0",
                    "trained_at": "2024-12-01T00:00:00Z",
                    "data_hash": "sha256:efgh5678",
                    "methodology": "LP only",
                    "n_observations": 18,
                    "r_squared": 0.60,
                    "is_active": False,
                    "backtest_metrics": {
                        "coverage_80": 0.82,
                        "coverage_95": 0.89,
                        "brier_score": 0.18
                    }
                }
            ]
            
            for version_data in mock_versions:
                if include_inactive or version_data["is_active"]:
                    versions.append(ModelVersion(**version_data))
            
            return versions
            
        except Exception as e:
            logger.error(f"Erro ao listar versões: {str(e)}", exc_info=True)
            raise
    
    async def get_version(self, version: str) -> Optional[ModelVersion]:
        """Obter versão específica"""
        try:
            versions = await self.list_versions(include_inactive=True)
            
            for model_version in versions:
                if model_version.version == version:
                    return model_version
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter versão {version}: {str(e)}", exc_info=True)
            raise
    
    async def get_active_model(self) -> Optional[ModelVersion]:
        """Obter modelo ativo"""
        try:
            versions = await self.list_versions(include_inactive=False)
            
            for model_version in versions:
                if model_version.is_active:
                    return model_version
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter modelo ativo: {str(e)}", exc_info=True)
            raise
    
    async def activate_version(self, version: str) -> bool:
        """Ativar versão específica"""
        try:
            # Verificar se versão existe
            model_version = await self.get_version(version)
            if not model_version:
                return False
            
            # TODO: Implementar ativação real
            # Por enquanto, apenas simular sucesso
            logger.info(f"Ativando versão {version}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao ativar versão {version}: {str(e)}", exc_info=True)
            raise
    
    async def load_model(self, version: str) -> Any:
        """Carregar modelo específico"""
        try:
            # TODO: Implementar carregamento real do modelo
            # Por enquanto, retornar objeto mock
            logger.info(f"Carregando modelo {version}")
            
            # Simular modelo
            class MockModel:
                def __init__(self, version):
                    self.version = version
                    self.loaded_at = datetime.utcnow()
                
                def predict(self, data):
                    # Simular previsão
                    return {"prediction": "mock"}
            
            return MockModel(version)
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {version}: {str(e)}", exc_info=True)
            raise
    
    async def get_version_performance(self, version: str) -> Optional[Dict[str, Any]]:
        """Obter performance de versão específica"""
        try:
            model_version = await self.get_version(version)
            if not model_version:
                return None
            
            return {
                "version": version,
                "metrics": model_version.backtest_metrics,
                "trained_at": model_version.trained_at,
                "methodology": model_version.methodology
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter performance da versão {version}: {str(e)}", exc_info=True)
            raise
    
    async def get_all_performance(self) -> Dict[str, Any]:
        """Obter performance de todas as versões"""
        try:
            versions = await self.list_versions(include_inactive=True)
            
            performance = {
                "versions": [],
                "summary": {
                    "total_versions": len(versions),
                    "active_versions": len([v for v in versions if v.is_active])
                }
            }
            
            for version in versions:
                perf_data = {
                    "version": version.version,
                    "is_active": version.is_active,
                    "metrics": version.backtest_metrics,
                    "trained_at": version.trained_at
                }
                performance["versions"].append(perf_data)
            
            return performance
            
        except Exception as e:
            logger.error(f"Erro ao obter performance de todas as versões: {str(e)}", exc_info=True)
            raise
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Obter metadados dos modelos"""
        try:
            return {
                "total_models": 2,
                "active_models": 1,
                "methodologies": ["LP primary, BVAR fallback", "LP only"],
                "data_sources": ["FRED", "BCB"],
                "last_training": "2025-01-01T00:00:00Z",
                "supported_versions": ["v1.0.0", "v0.9.0"]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter metadados: {str(e)}", exc_info=True)
            raise
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Obter capacidades dos modelos"""
        try:
            return {
                "supported_horizons": list(range(1, 13)),
                "supported_fed_moves": list(range(-200, 201, 25)),
                "confidence_levels": [0.80, 0.95],
                "discretization": 25,
                "max_batch_size": self.settings.MAX_BATCH_SIZE,
                "supported_regimes": ["normal", "stress", "crisis", "recovery"],
                "data_requirements": {
                    "min_observations": 10,
                    "max_observations": 50,
                    "frequency": "monthly"
                },
                "limitations": [
                    "Alta incerteza com amostras pequenas",
                    "Bandas de confiança largas",
                    "Dependência de dados históricos"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter capacidades: {str(e)}", exc_info=True)
            raise