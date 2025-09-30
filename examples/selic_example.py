#!/usr/bin/env python3
"""
Exemplo de uso dos dados da Selic
Demonstra como acessar e trabalhar com os dados da Selic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.selic_service import SelicService
from src.types.selic_types import SelicRateType, CopomMeeting
from datetime import datetime, timedelta

def main():
    """Exemplo principal"""
    print("🇧🇷 EXEMPLO DE USO DOS DADOS DA SELIC")
    print("=" * 50)
    
    # Inicializar serviço
    service = SelicService()
    
    try:
        # Carregar dados
        print("\n📊 Carregando dados da Selic...")
        data = service.load_data()
        accessor = service.get_accessor()
        
        # 1. Selic atual e básica
        print("\n💰 SELIC ATUAL:")
        selic_current = accessor.get_selic_current()
        print(f"   Taxa atual: {selic_current:.2f}%")
        
        selic = accessor.get_selic()
        print(f"   Período: {selic.index[0].date()} a {selic.index[-1].date()}")
        print(f"   Taxa média: {selic.mean():.2f}%")
        print(f"   Volatilidade: {selic.std():.2f}%")
        
        # 2. Mudanças recentes
        print("\n📊 MUDANÇAS RECENTES:")
        selic_change_1m = accessor.get_selic_change(1)
        selic_change_3m = accessor.get_selic_change(3)
        selic_change_12m = accessor.get_selic_change(12)
        
        print(f"   Mudança 1 mês: {selic_change_1m.iloc[-1]:.2f}%")
        print(f"   Mudança 3 meses: {selic_change_3m.iloc[-1]:.2f}%")
        print(f"   Mudança 12 meses: {selic_change_12m.iloc[-1]:.2f}%")
        
        # 3. Tendência e volatilidade
        print("\n📈 ANÁLISE DE TENDÊNCIAS:")
        trend = accessor.get_selic_trend()
        volatility = accessor.get_selic_volatility()
        rate_range = accessor.get_selic_range()
        
        print(f"   Tendência: {trend}")
        print(f"   Volatilidade: {volatility:.2f}%")
        print(f"   Range (últimos 12 meses): {rate_range[0]:.2f}% - {rate_range[1]:.2f}%")
        
        # 4. IPCA se disponível
        print("\n📊 IPCA:")
        if accessor.get_ipca_current() is not None:
            ipca_current = accessor.get_ipca_current()
            ipca_yoy = accessor.get_ipca_yoy().iloc[-1]
            print(f"   IPCA atual: {ipca_current:.2f}")
            print(f"   IPCA acumulado 12 meses: {ipca_yoy:.2f}%")
        else:
            print("   IPCA não disponível")
        
        # 5. Decisões do Copom
        print("\n🏛️ DECISÕES DO COPOM:")
        copom_summary = service.get_copom_summary()
        print(f"   Total de decisões: {copom_summary['total_decisions']}")
        print(f"   Decisões recentes (12 meses): {copom_summary['recent_decisions_count']}")
        
        if copom_summary['decision_counts']:
            print("   Distribuição por tipo:")
            for decision_type, count in copom_summary['decision_counts'].items():
                print(f"     {decision_type}: {count}")
        
        print("   Últimas decisões:")
        for decision in copom_summary['last_decisions']:
            print(f"     {decision['date'][:10]}: {decision['decision']} ({decision['change_bps']:+d} bps) → {decision['selic_after']:.2f}%")
        
        # 6. Ciclos da Selic
        print("\n🔄 CICLOS DA SELIC:")
        cycle_summary = service.get_cycle_summary()
        print(f"   Total de ciclos: {cycle_summary['total_cycles']}")
        
        if cycle_summary['cycle_counts']:
            print("   Distribuição por tipo:")
            for cycle_type, count in cycle_summary['cycle_counts'].items():
                print(f"     {cycle_type}: {count}")
        
        if 'current_cycle' in cycle_summary:
            current = cycle_summary['current_cycle']
            print(f"   Ciclo atual:")
            print(f"     Início: {current['start_date'][:10]}")
            print(f"     Tipo: {current['cycle_type']}")
            print(f"     Duração: {current['duration_months']} meses")
            print(f"     Mudança total: {current['total_change_bps']:+d} bps")
        
        print("   Ciclos recentes:")
        for cycle in cycle_summary['recent_cycles']:
            print(f"     {cycle['start_date'][:10]} a {cycle['end_date'][:10]}: {cycle['cycle_type']} ({cycle['total_change_bps']:+d} bps, {cycle['duration_months']} meses)")
        
        # 7. Estatísticas por período
        print("\n📊 ESTATÍSTICAS POR PERÍODO:")
        
        # Último ano
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        selic_year = accessor.get_selic(start_date, end_date)
        print(f"   Último ano:")
        print(f"     Média: {selic_year.mean():.2f}%")
        print(f"     Volatilidade: {selic_year.std():.2f}%")
        print(f"     Range: {selic_year.min():.2f}% - {selic_year.max():.2f}%")
        
        # Últimos 5 anos
        start_date_5y = end_date - timedelta(days=5*365)
        selic_5y = accessor.get_selic(start_date_5y, end_date)
        print(f"   Últimos 5 anos:")
        print(f"     Média: {selic_5y.mean():.2f}%")
        print(f"     Volatilidade: {selic_5y.std():.2f}%")
        print(f"     Range: {selic_5y.min():.2f}% - {selic_5y.max():.2f}%")
        
        # 8. Resumo completo
        print("\n📋 RESUMO COMPLETO:")
        summary = service.get_selic_summary()
        
        print(f"   Taxa atual: {summary['current']:.2f}%")
        print(f"   Taxa média: {summary['mean']:.2f}%")
        print(f"   Volatilidade: {summary['volatility']:.2f}%")
        print(f"   Range: {summary['min']:.2f}% - {summary['max']:.2f}%")
        print(f"   Tendência: {summary['trend']}")
        print(f"   Observações: {summary['observations']}")
        
        if 'current_cycle_type' in summary:
            print(f"   Ciclo atual: {summary['current_cycle_type']}")
        
        if 'ipca_current' in summary:
            print(f"   IPCA atual: {summary['ipca_current']:.2f}")
            print(f"   IPCA acumulado: {summary['ipca_yoy']:.2f}%")
        
        print("\n✅ Exemplo da Selic concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
