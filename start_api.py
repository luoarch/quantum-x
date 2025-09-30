#!/usr/bin/env python3
"""
Script para iniciar a API FED-Selic
"""

import uvicorn
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def main():
    """Iniciar a API"""
    print("🚀 Iniciando API FED-Selic...")
    print("=" * 50)
    
    # Configurações
    host = "0.0.0.0"
    port = 8000
    reload = True
    log_level = "info"
    
    print(f"📍 Host: {host}")
    print(f"📍 Porta: {port}")
    print(f"📍 Reload: {reload}")
    print(f"📍 Log Level: {log_level}")
    print(f"📍 Docs: http://{host}:{port}/docs")
    print(f"📍 Health: http://{host}:{port}/health")
    print("=" * 50)
    
    try:
        # Iniciar servidor
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 API interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
