"""
Redis Cache Manager - High Performance Caching
"""
import redis
import json
import pickle
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import logging

from .config import config

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager for high performance"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(
                config.redis.url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return json.dumps(data).encode('utf-8')
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        try:
            return pickle.loads(data)
        except Exception:
            try:
                return json.loads(data.decode('utf-8'))
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with optional TTL"""
        try:
            serialized = self._serialize(value)
            ttl = ttl or config.cache_ttl_seconds
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            return self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    # Network Effects specific cache methods
    def cache_client_stats(self, client_id: str, stats: Dict[str, Any]) -> bool:
        """Cache client statistics"""
        key = f"client_stats:{client_id}"
        return self.set(key, stats, ttl=3600)  # 1 hour
    
    def get_client_stats(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get cached client statistics"""
        key = f"client_stats:{client_id}"
        return self.get(key)
    
    def cache_network_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Cache network metrics"""
        key = "network_metrics:latest"
        return self.set(key, metrics, ttl=1800)  # 30 minutes
    
    def get_network_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached network metrics"""
        key = "network_metrics:latest"
        return self.get(key)
    
    def cache_prediction_result(self, prediction_id: str, result: Dict[str, Any]) -> bool:
        """Cache prediction result"""
        key = f"prediction:{prediction_id}"
        return self.set(key, result, ttl=7200)  # 2 hours
    
    def get_prediction_result(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction result"""
        key = f"prediction:{prediction_id}"
        return self.get(key)
    
    def cache_model_version(self, version: str, model_data: Dict[str, Any]) -> bool:
        """Cache model version data"""
        key = f"model_version:{version}"
        return self.set(key, model_data, ttl=86400)  # 24 hours
    
    def get_model_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get cached model version data"""
        key = f"model_version:{version}"
        return self.get(key)
    
    def cache_retrain_status(self, status: Dict[str, Any]) -> bool:
        """Cache retraining status"""
        key = "retrain_status"
        return self.set(key, status, ttl=300)  # 5 minutes
    
    def get_retrain_status(self) -> Optional[Dict[str, Any]]:
        """Get cached retraining status"""
        key = "retrain_status"
        return self.get(key)
    
    def invalidate_client_cache(self, client_id: str) -> bool:
        """Invalidate all cache for a client"""
        try:
            pattern = f"*client*{client_id}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    def invalidate_network_cache(self) -> bool:
        """Invalidate network-related cache"""
        try:
            patterns = ["network_metrics:*", "retrain_status", "model_version:*"]
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Network cache invalidation error: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

# Global cache manager instance
cache_manager = CacheManager()
