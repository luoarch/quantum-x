#!/usr/bin/env python3
"""
Exemplo de uso das taxas de juros
Demonstra como acessar e trabalhar com os dados de taxas de juros
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.interest_rate_service import InterestRateService
from src.types.interest_rates import InterestRateType
from datetime import datetime, timedelta

def main():
    """Exemplo principal"""
    print("🎯 EXEMPLO DE USO DAS TAXAS DE JUROS")
    print("=" * 50)
    
    # Inicializar serviço
    service = InterestRateService()
    
    try:
        # Carregar dados
        print("\n📊 Carregando dados...")
        data = service.load_data()
        accessor = service.get_accessor()
        
        # 1. Taxas atuais
        print("\n💰 TAXAS ATUAIS:")
        current_rates = service.get_current_rates()
        for rate_name, rate_value in current_rates.items():
            print(f"   {rate_name}: {rate_value:.2f}%")
        
        # 2. Fed Funds Rate
        print("\n🏦 FED FUNDS RATE:")
        fed_funds = accessor.get_fed_funds()
        print(f"   Período: {fed_funds.index[0].date()} a {fed_funds.index[-1].date()}")
        print(f"   Taxa atual: {fed_funds.iloc[-1]:.2f}%")
        print(f"   Taxa média: {fed_funds.mean():.2f}%")
        print(f"   Volatilidade: {fed_funds.std():.2f}%")
        
        # 3. Selic
        print("\n🇧🇷 SELIC:")
        selic = accessor.get_selic()
        print(f"   Período: {selic.index[0].date()} a {selic.index[-1].date()}")
        print(f"   Taxa atual: {selic.iloc[-1]:.2f}%")
        print(f"   Taxa média: {selic.mean():.2f}%")
        print(f"   Volatilidade: {selic.std():.2f}%")
        
        # 4. Treasury Rates
        print("\n📈 TREASURY RATES:")
        treasury_rates = ['3M', '2Y', '10Y']
        for rate_name in treasury_rates:
            try:
                rate_type = getattr(InterestRateType, f'TREASURY_{rate_name}')
                rate_series = accessor.get_treasury_rate(rate_type)
                print(f"   {rate_name}: {rate_series.iloc[-1]:.2f}% (média: {rate_series.mean():.2f}%)")
            except:
                print(f"   {rate_name}: Não disponível")
        
        # 5. Spreads
        print("\n📊 SPREADS:")
        fed_selic_spread = accessor.get_fed_selic_spread()
        print(f"   Fed-Selic: {fed_selic_spread.iloc[-1]:.2f}% (média: {fed_selic_spread.mean():.2f}%)")
        
        try:
            treasury_spread = accessor.get_treasury_spread(
                InterestRateType.TREASURY_10Y, 
                InterestRateType.TREASURY_2Y
            )
            print(f"   10Y-2Y Treasury: {treasury_spread.iloc[-1]:.2f}% (média: {treasury_spread.mean():.2f}%)")
        except:
            print("   10Y-2Y Treasury: Não disponível")
        
        # 6. Curva de juros atual
        print("\n📈 CURVA DE JUROS ATUAL:")
        yield_curve = accessor.get_yield_curve()
        print(f"   Data: {yield_curve.date.date()}")
        print(f"   Slope 2Y-10Y: {yield_curve.slope_2y10y:.2f}%")
        print(f"   Slope 3M-10Y: {yield_curve.slope_3m10y:.2f}%")
        print(f"   Pontos da curva: {len(yield_curve.points)}")
        
        # 7. Mudanças recentes
        print("\n📊 MUDANÇAS RECENTES (últimos 3 meses):")
        fed_change = accessor.get_fed_funds_change(3)
        selic_change = accessor.get_selic_change(3)
        
        print(f"   Fed Funds (3M): {fed_change.iloc[-1]:.2f}%")
        print(f"   Selic (3M): {selic_change.iloc[-1]:.2f}%")
        
        # 8. Estatísticas por período
        print("\n📊 ESTATÍSTICAS POR PERÍODO:")
        
        # Último ano
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        fed_year = accessor.get_fed_funds(start_date, end_date)
        selic_year = accessor.get_selic(start_date, end_date)
        
        print(f"   Último ano:")
        print(f"     Fed Funds: {fed_year.mean():.2f}% ± {fed_year.std():.2f}%")
        print(f"     Selic: {selic_year.mean():.2f}% ± {selic_year.std():.2f}%")
        
        # 9. Resumo completo
        print("\n📋 RESUMO COMPLETO:")
        summary = service.get_rate_summary()
        
        for rate_name, stats in summary.items():
            print(f"   {rate_name}:")
            print(f"     Atual: {stats['current']:.2f}%")
            print(f"     Média: {stats['mean']:.2f}%")
            print(f"     Volatilidade: {stats['std']:.2f}%")
            print(f"     Range: {stats['min']:.2f}% - {stats['max']:.2f}%")
        
        print("\n✅ Exemplo concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
