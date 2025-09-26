#!/usr/bin/env python3
"""
Setup Enterprise Infrastructure
PostgreSQL + Redis + RabbitMQ + Database Schema
"""
import sys
import os
import subprocess
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enterprise.database import db_manager
from src.enterprise.cache import cache_manager
from src.enterprise.queue import queue_manager
from src.enterprise.models import Client
from src.enterprise.config import config

def check_postgres():
    """Check PostgreSQL connection"""
    print("🔍 Verificando PostgreSQL...")
    try:
        healthy = db_manager.health_check()
        if healthy:
            print("✅ PostgreSQL conectado")
            return True
        else:
            print("❌ PostgreSQL não conectado")
            return False
    except Exception as e:
        print(f"❌ Erro PostgreSQL: {e}")
        return False

def check_redis():
    """Check Redis connection"""
    print("🔍 Verificando Redis...")
    try:
        healthy = cache_manager.health_check()
        if healthy:
            print("✅ Redis conectado")
            return True
        else:
            print("❌ Redis não conectado")
            return False
    except Exception as e:
        print(f"❌ Erro Redis: {e}")
        return False

def check_rabbitmq():
    """Check RabbitMQ connection"""
    print("🔍 Verificando RabbitMQ...")
    try:
        healthy = queue_manager.health_check()
        if healthy:
            print("✅ RabbitMQ conectado")
            return True
        else:
            print("❌ RabbitMQ não conectado")
            return False
    except Exception as e:
        print(f"❌ Erro RabbitMQ: {e}")
        return False

def create_database_schema():
    """Create database schema"""
    print("🏗️ Criando schema do banco de dados...")
    try:
        # This will create all tables
        from src.enterprise.models import Base
        Base.metadata.create_all(bind=db_manager.engine)
        print("✅ Schema criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar schema: {e}")
        return False

def test_enterprise_system():
    """Test the complete enterprise system"""
    print("🧪 Testando sistema enterprise...")
    try:
        # Test database operations
        import uuid
        test_client = {
            'client_id': f'test_enterprise_{uuid.uuid4().hex[:8]}',
            'institution': 'Test Institution',
            'client_type': 'test',
            'client_metadata': {'test': True}
        }
        
        client = db_manager.create_client(test_client)
        if client:
            print("✅ Database operations funcionando")
        else:
            print("❌ Database operations falharam")
            return False
        
        # Test cache operations
        cache_manager.set('test_key', {'test': 'data'}, ttl=60)
        cached_data = cache_manager.get('test_key')
        if cached_data and cached_data.get('test') == 'data':
            print("✅ Cache operations funcionando")
        else:
            print("❌ Cache operations falharam")
            return False
        
        # Test queue operations
        queue_manager.publish_analytics_update({'test': 'message'})
        print("✅ Queue operations funcionando")
        
        # Cleanup test data (simplified)
        cache_manager.delete('test_key')
        
        print("✅ Sistema enterprise funcionando perfeitamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Main setup function"""
    print("🏗️ CONFIGURAÇÃO DO SISTEMA ENTERPRISE")
    print("=" * 50)
    
    # Check all services
    postgres_ok = check_postgres()
    redis_ok = check_redis()
    rabbitmq_ok = check_rabbitmq()
    
    if not all([postgres_ok, redis_ok, rabbitmq_ok]):
        print("\n❌ Serviços não disponíveis. Verifique:")
        print("   - PostgreSQL rodando na porta 5432")
        print("   - Redis rodando na porta 6379")
        print("   - RabbitMQ rodando na porta 5672")
        print("\nPara iniciar os serviços:")
        print("   docker-compose up -d postgres redis rabbitmq")
        return False
    
    # Create database schema
    if not create_database_schema():
        return False
    
    # Test system
    if not test_enterprise_system():
        return False
    
    print("\n🎉 SISTEMA ENTERPRISE CONFIGURADO COM SUCESSO!")
    print("=" * 50)
    print("✅ PostgreSQL: Schema criado")
    print("✅ Redis: Cache funcionando")
    print("✅ RabbitMQ: Queues configuradas")
    print("✅ Database: Tabelas criadas")
    print("\n🚀 Para iniciar a API enterprise:")
    print("   python api_enterprise.py")
    print("\n🌐 Endpoints disponíveis:")
    print("   - http://localhost:5000/api/health")
    print("   - http://localhost:5000/enterprise")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
