"""
Cache Service - Single Responsibility Principle
Serviço responsável por cache de previsões e dados
"""

from typing import Dict, Any, Optional
import json
import hashlib
from datetime import datetime, timedelta

from src.core.interfaces import ICacheService
from src.core.exceptions import CacheError

class RedisCacheService(ICacheService):
    """
    Serviço de cache usando Redis
    
    Responsabilidades:
    - Cache de previsões
    - Cache de modelos
    - Invalidação de cache
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Inicializar cliente Redis"""
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url)
            # Testar conexão
            self.redis_client.ping()
        except ImportError:
            # Fallback para cache em memória se Redis não disponível
            self.redis_client = None
            self._memory_cache = {}
        except Exception as e:
            print(f"⚠️  Redis não disponível, usando cache em memória: {e}")
            self.redis_client = None
            self._memory_cache = {}
    
    async def get_cached_prediction(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obter previsão do cache"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Cache em memória
                return self._memory_cache.get(cache_key)
            
            return None
            
        except Exception as e:
            raise CacheError(f"Erro ao obter cache: {str(e)}", operation="get", key=cache_key)
    
    async def cache_prediction(self, 
                             cache_key: str, 
                             prediction: Dict[str, Any], 
                             ttl_seconds: int) -> None:
        """Cachear previsão"""
        try:
            # Serializar dados
            serialized_data = json.dumps(prediction, default=str)
            
            if self.redis_client:
                self.redis_client.setex(cache_key, ttl_seconds, serialized_data)
            else:
                # Cache em memória com TTL simplificado
                self._memory_cache[cache_key] = {
                    'data': prediction,
                    'expires_at': datetime.now() + timedelta(seconds=ttl_seconds)
                }
            
        except Exception as e:
            raise CacheError(f"Erro ao cachear: {str(e)}", operation="set", key=cache_key)
    
    async def invalidate_model_cache(self, model_version: str) -> None:
        """Invalidar cache do modelo"""
        try:
            pattern = f"prediction:*model_version:{model_version}*"
            
            if self.redis_client:
                # Buscar chaves que correspondem ao padrão
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Cache em memória - remover chaves que contêm a versão
                keys_to_remove = [k for k in self._memory_cache.keys() if model_version in k]
                for key in keys_to_remove:
                    del self._memory_cache[key]
            
        except Exception as e:
            raise CacheError(f"Erro ao invalidar cache: {str(e)}", operation="invalidate")
    
    def generate_cache_key(self, 
                          fed_decision_date: str, 
                          fed_move_bps: int, 
                          horizons_months: list, 
                          model_version: str) -> str:
        """Gerar chave de cache"""
        key_data = {
            "fed_decision_date": fed_decision_date,
            "fed_move_bps": fed_move_bps,
            "horizons_months": sorted(horizons_months),
            "model_version": model_version
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"prediction:{key_hash}"
    
    async def cleanup_expired(self) -> int:
        """Limpar entradas expiradas (apenas para cache em memória)"""
        if self.redis_client:
            return 0  # Redis gerencia TTL automaticamente
        
        # Limpar cache em memória
        now = datetime.now()
        expired_keys = []
        
        for key, value in self._memory_cache.items():
            if isinstance(value, dict) and 'expires_at' in value:
                if value['expires_at'] < now:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        return len(expired_keys)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    "backend": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            else:
                return {
                    "backend": "memory",
                    "total_keys": len(self._memory_cache),
                    "expired_keys": await self.cleanup_expired()
                }
                
        except Exception as e:
            return {
                "backend": "unknown",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup do serviço"""
        if self.redis_client:
            self.redis_client.close()
        else:
            self._memory_cache.clear()
