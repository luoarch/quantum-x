"""
Teste de Cobertura 100% - APIs Corrigidas
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.robust_data_collector import RobustDataCollector


async def test_100_coverage():
    """Testa cobertura 100% com APIs corrigidas"""
    
    print("🚀 TESTE DE COBERTURA 100% - APIs CORRIGIDAS")
    print("=" * 60)
    
    # Inicializar banco de dados
    db = SessionLocal()
    
    try:
        # Inicializar coletor robusto
        collector = RobustDataCollector(db)
        
        # Verificar status de saúde das fontes
        print("\n🏥 VERIFICANDO STATUS DE SAÚDE DAS FONTES")
        print("-" * 50)
        
        health_status = await collector.get_health_status()
        
        for source_name, status in health_status.items():
            status_emoji = "✅" if status['status'] == 'healthy' else "❌" if status['status'] == 'unhealthy' else "⚠️"
            print(f"{status_emoji} {source_name.upper()}: {status['status']}")
            if 'error' in status:
                print(f"   Erro: {status['error']}")
            if 'test_records' in status:
                print(f"   Registros de teste: {status['test_records']}")
        
        # Testar coleta de todas as séries
        print("\n📊 TESTANDO COLETA DE TODAS AS SÉRIES")
        print("-" * 50)
        
        results = await collector.collect_all_series(months=12)
        
        # Exibir resultados
        print(f"\n📈 RESUMO DA COLETA")
        print(f"Total de séries: {results['summary']['total_series']}")
        print(f"Séries bem-sucedidas: {results['summary']['successful_series']}")
        print(f"Total de registros: {results['summary']['total_records']}")
        
        print(f"\n🔍 DETALHES POR SÉRIE:")
        for series_name, result in results['results'].items():
            status_emoji = "✅" if result['status'] in ['success', 'success_with_fallback'] else "❌"
            print(f"{status_emoji} {series_name.upper()}: {result['status']} ({result.get('records', 0)} registros)")
            
            if 'source' in result and result['source']:
                print(f"   Fonte: {result['source']}")
            
            if 'results' in result:
                for source_name, source_result in result['results'].items():
                    if source_name != 'cross_validation':
                        source_status = "✅" if source_result['status'] == 'success' else "❌"
                        print(f"   {source_status} {source_name}: {source_result.get('records', 0)} registros")
                
                # Mostrar validação cruzada se disponível
                if 'cross_validation' in result['results']:
                    cv = result['results']['cross_validation']
                    if cv['discrepancy_detected']:
                        print(f"   ⚠️ Validação cruzada: {cv['discrepancy_percent']:.2f}% discrepância")
                    else:
                        print(f"   ✅ Validação cruzada: OK")
        
        # Verificar se atingimos 100% de cobertura
        successful_series = results['summary']['successful_series']
        total_series = results['summary']['total_series']
        coverage_percent = (successful_series / total_series) * 100
        
        print(f"\n🎯 COBERTURA FINAL: {coverage_percent:.1f}%")
        
        if coverage_percent == 100.0:
            print("🎉 PARABÉNS! Cobertura 100% atingida!")
        elif coverage_percent >= 80.0:
            print("✅ Boa cobertura! Quase lá!")
        else:
            print("⚠️ Cobertura baixa. Verificar APIs.")
        
        # Testar coleta individual de séries problemáticas
        print(f"\n🔧 TESTANDO SÉRIES INDIVIDUAIS")
        print("-" * 50)
        
        problem_series = ['cambio', 'desemprego', 'cli']
        
        for series_name in problem_series:
            print(f"\n🔄 Testando {series_name.upper()}...")
            
            try:
                result = await collector.collect_series_with_priority(series_name, months=6)
                
                if result['status'] in ['success', 'success_with_fallback']:
                    print(f"   ✅ Sucesso: {result['records']} registros")
                    print(f"   Fonte: {result['source']}")
                    
                    # Mostrar amostra dos dados
                    if not result['data'].empty:
                        print(f"   Últimos 3 valores:")
                        last_3 = result['data'].tail(3)
                        for _, row in last_3.iterrows():
                            print(f"     {row['date'].strftime('%Y-%m-%d')}: {row['value']:.4f}")
                else:
                    print(f"   ❌ Falha: {result['status']}")
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return None
        
    finally:
        db.close()


async def main():
    """Função principal"""
    results = await test_100_coverage()
    
    if results:
        print(f"\n📄 Relatório completo salvo em memória")
        print(f"Timestamp: {results['summary']['timestamp']}")
    else:
        print(f"\n❌ Teste falhou")


if __name__ == "__main__":
    asyncio.run(main())
