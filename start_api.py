#!/usr/bin/env python3
"""
Script para iniciar a API de Spillovers Econômicos
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(__file__))

# Importar e executar a API
from api.app import app

if __name__ == '__main__':
    print("🚀 Iniciando API de Spillovers Econômicos...")
    print("🌐 Acesse: http://localhost:3000")
    print("📊 Dashboard: http://localhost:3000")
    print("🔗 API Docs: http://localhost:3000/api/health")
    app.run(debug=True, host='0.0.0.0', port=3000)
