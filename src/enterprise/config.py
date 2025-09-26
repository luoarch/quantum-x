"""
Enterprise Configuration - Type Safe
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class DatabaseConfig(BaseSettings):
    """PostgreSQL Configuration"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="spillover_network", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="postgres", env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class RedisConfig(BaseSettings):
    """Redis Configuration"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

class RabbitMQConfig(BaseSettings):
    """RabbitMQ Configuration"""
    host: str = Field(default="localhost", env="RABBITMQ_HOST")
    port: int = Field(default=5672, env="RABBITMQ_PORT")
    user: str = Field(default="guest", env="RABBITMQ_USER")
    password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    vhost: str = Field(default="/", env="RABBITMQ_VHOST")
    
    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"

class EnterpriseConfig(BaseSettings):
    """Main Enterprise Configuration"""
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    
    # Network Effects Settings
    min_clients_for_retrain: int = Field(default=10, env="MIN_CLIENTS_RETRAIN")
    min_predictions_for_retrain: int = Field(default=100, env="MIN_PREDICTIONS_RETRAIN")
    retrain_frequency_hours: int = Field(default=24, env="RETRAIN_FREQUENCY_HOURS")
    
    # Cache Settings
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Queue Settings
    prediction_queue: str = Field(default="network_predictions", env="PREDICTION_QUEUE")
    retrain_queue: str = Field(default="model_retrain", env="RETRAIN_QUEUE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

# Global config instance
config = EnterpriseConfig()
