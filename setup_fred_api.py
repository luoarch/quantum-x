#!/usr/bin/env python3
"""
Script para configurar FRED API Key
Execute: python setup_fred_api.py
"""

import os
import sys
from pathlib import Path

def setup_fred_api():
    """Configura FRED API Key"""
    print("🔑 Configuração da FRED API Key")
    print("=" * 50)
    
    # Verificar se já existe
    current_key = os.getenv('FRED_API_KEY')
    if current_key and current_key != 'your_fred_api_key_here':
        print(f"✅ FRED_API_KEY já configurada: {current_key[:10]}...")
        return True
    
    print("📋 Para obter uma FRED API Key gratuita:")
    print("1. Acesse: https://fred.stlouisfed.org/docs/api/api_key.html")
    print("2. Registre-se gratuitamente")
    print("3. Copie sua API key")
    print()
    
    # Solicitar API key
    api_key = input("🔑 Cole sua FRED API Key aqui: ").strip()
    
    if not api_key:
        print("❌ API Key não fornecida")
        return False
    
    if api_key == 'your_fred_api_key_here':
        print("❌ API Key inválida (valor padrão)")
        return False
    
    # Configurar variável de ambiente
    os.environ['FRED_API_KEY'] = api_key
    
    # Salvar no arquivo de configuração
    config_file = Path("config.env")
    if config_file.exists():
        # Atualizar arquivo existente
        content = config_file.read_text()
        if "FRED_API_KEY=" in content:
            content = content.replace("FRED_API_KEY=your_fred_api_key_here", f"FRED_API_KEY={api_key}")
        else:
            content += f"\nFRED_API_KEY={api_key}\n"
        config_file.write_text(content)
    else:
        # Criar novo arquivo
        config_file.write_text(f"FRED_API_KEY={api_key}\n")
    
    print(f"✅ FRED_API_KEY configurada: {api_key[:10]}...")
    print("💾 Configuração salva em config.env")
    
    return True

def test_fred_api():
    """Testa a FRED API"""
    print("\n🧪 Testando FRED API...")
    
    try:
        import httpx
        import asyncio
        
        async def test_api():
            api_key = os.getenv('FRED_API_KEY')
            if not api_key:
                print("❌ FRED_API_KEY não encontrada")
                return False
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'OECDCLI',
                'api_key': api_key,
                'file_type': 'json',
                'limit': 5
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data:
                        print(f"✅ FRED API funcionando! {len(data['observations'])} observações encontradas")
                        return True
                    else:
                        print("❌ Resposta inválida da FRED API")
                        return False
                else:
                    print(f"❌ Erro HTTP {response.status_code}: {response.text[:100]}")
                    return False
        
        result = asyncio.run(test_api())
        return result
        
    except Exception as e:
        print(f"❌ Erro ao testar FRED API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quantum X - Configuração FRED API")
    print("=" * 50)
    
    # Configurar API key
    if setup_fred_api():
        print("\n" + "=" * 50)
        
        # Testar API
        if test_fred_api():
            print("\n🎉 Configuração concluída com sucesso!")
            print("💡 Agora você pode usar a FRED API para dados CLI")
            print("🔄 Reinicie o servidor para aplicar as mudanças")
        else:
            print("\n⚠️ Configuração salva, mas teste da API falhou")
            print("🔍 Verifique se a API key está correta")
    else:
        print("\n❌ Configuração cancelada")
        sys.exit(1)
