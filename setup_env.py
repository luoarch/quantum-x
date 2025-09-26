#!/usr/bin/env python3
"""
Setup Environment Configuration
Adiciona configurações enterprise ao .env
"""
import os

def setup_env_file():
    """Setup .env file with enterprise configuration"""
    
    env_content = """# Spillover AI - Enterprise Configuration
# Network Effects Moats System

# =============================================================================
# FRED API CONFIGURATION
# =============================================================================
FRED_API_KEY=90157114039846fe14d8993faa2f11c7

# =============================================================================
# DATABASE CONFIGURATION (PostgreSQL)
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=spillover_network
DB_USER=postgres
DB_PASSWORD=postgres

# =============================================================================
# REDIS CONFIGURATION (Cache)
# =============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# =============================================================================
# RABBITMQ CONFIGURATION (Message Queue)
# =============================================================================
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# =============================================================================
# NETWORK EFFECTS CONFIGURATION
# =============================================================================
# Minimum clients required for retraining
MIN_CLIENTS_RETRAIN=10

# Minimum predictions required for retraining
MIN_PREDICTIONS_RETRAIN=100

# Retraining frequency in hours
RETRAIN_FREQUENCY_HOURS=24

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================
# Cache TTL in seconds (1 hour default)
CACHE_TTL_SECONDS=3600

# =============================================================================
# QUEUE CONFIGURATION
# =============================================================================
# Queue names for different operations
PREDICTION_QUEUE=network_predictions
RETRAIN_QUEUE=model_retrain

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
# Debug mode
DEBUG=False

# Log level
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# Model storage path
MODEL_PATH=models/

# Model version
MODEL_VERSION=1.0.0

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================
# Enable metrics collection
ENABLE_METRICS=True

# Metrics port
METRICS_PORT=9090

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
# Secret key for sessions
SECRET_KEY=your-secret-key-here-change-in-production

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# =============================================================================
# PRODUCTION OVERRIDES
# =============================================================================
# Uncomment and modify for production deployment

# DB_HOST=your-production-db-host
# DB_PASSWORD=your-production-db-password
# REDIS_HOST=your-production-redis-host
# RABBITMQ_HOST=your-production-rabbitmq-host
# SECRET_KEY=your-production-secret-key
"""
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("📝 Arquivo .env já existe. Fazendo backup...")
        os.rename('.env', '.env.backup')
        print("✅ Backup criado: .env.backup")
    
    # Write new .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env configurado com sucesso!")
    print("🔧 Configurações enterprise adicionadas:")
    print("   - PostgreSQL: localhost:5432")
    print("   - Redis: localhost:6379")
    print("   - RabbitMQ: localhost:5672")
    print("   - Network Effects: Configurado")
    print("   - Cache: 1 hora TTL")
    print("   - Queues: Configuradas")
    
    return True

if __name__ == "__main__":
    print("🔧 CONFIGURANDO ARQUIVO .ENV")
    print("=" * 40)
    
    try:
        setup_env_file()
        print("\n🎉 Configuração concluída!")
        print("\n📋 Próximos passos:")
        print("   1. docker-compose -f docker-compose.enterprise.yml up -d")
        print("   2. python setup_enterprise.py")
        print("   3. python api_enterprise.py")
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        exit(1)
