#!/usr/bin/env python3
"""
Test Suite Consolidado - Quantum X Trading Signals
Executa todos os testes essenciais do sistema
"""

import sys
import subprocess
import time
from pathlib import Path

def run_test(test_file, description):
    """Executa um teste específico"""
    print(f"\n🧪 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCESSO")
            if result.stdout:
                print("📊 Saída:")
                print(result.stdout[-500:])  # Últimas 500 linhas
        else:
            print(f"❌ {description} - FALHOU")
            print("📋 Erro:")
            print(result.stderr[-500:])  # Últimas 500 linhas
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (5min)")
        return False
    except Exception as e:
        print(f"💥 {description} - ERRO: {e}")
        return False

def main():
    """Executa suite completa de testes"""
    print("🚀 QUANTUM X - TEST SUITE CONSOLIDADO")
    print("=" * 60)
    print("Executando todos os testes essenciais do sistema...")
    
    # Lista de testes essenciais
    tests = [
        ("test_advanced_strategy.py", "Estratégia Avançada (Markov-Switching + HRP)"),
        ("test_real_assets_backtest.py", "Backtesting com Ativos Reais"),
        ("test_robustness_system.py", "Sistema de Robustez 4-Camadas"),
        ("test_signal_generation_simple.py", "Geração de Sinais Básica")
    ]
    
    results = []
    start_time = time.time()
    
    for test_file, description in tests:
        if Path(test_file).exists():
            success = run_test(test_file, description)
            results.append((description, success))
        else:
            print(f"⚠️ {test_file} não encontrado - PULANDO")
            results.append((description, False))
    
    # Resumo final
    total_time = time.time() - start_time
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 RESUMO FINAL")
    print("=" * 60)
    print(f"⏱️  Tempo total: {total_time:.1f}s")
    print(f"✅ Testes aprovados: {passed}/{total}")
    print(f"📈 Taxa de sucesso: {passed/total*100:.1f}%")
    
    print(f"\n📋 DETALHES:")
    for description, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {status} - {description}")
    
    if passed == total:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema pronto para produção!")
    else:
        print(f"\n⚠️  {total-passed} TESTE(S) FALHARAM")
        print("🔧 Verifique os erros acima")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
