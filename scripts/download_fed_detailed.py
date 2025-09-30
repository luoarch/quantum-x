#!/usr/bin/env python3
"""
Script para baixar dados detalhados do Fed via FRED API
Inclui Federal Funds Rate, Treasury Rates, e outras séries relevantes
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import warnings

warnings.filterwarnings('ignore')

# Configuração da API FRED
FRED_API_KEY = '90157114039846fe14d8993faa2f11c7'
FRED_BASE_URL = 'https://api.stlouisfed.org/fred'

# Séries do Fed para download
FED_SERIES = {
    'FEDFUNDS': 'Federal Funds Effective Rate',
    'DFF': 'Federal Funds Rate (Daily)',
    'DGS1MO': '1-Month Treasury Rate',
    'DGS3MO': '3-Month Treasury Rate',
    'DGS6MO': '6-Month Treasury Rate',
    'DGS1': '1-Year Treasury Rate',
    'DGS2': '2-Year Treasury Rate',
    'DGS3': '3-Year Treasury Rate',
    'DGS5': '5-Year Treasury Rate',
    'DGS7': '7-Year Treasury Rate',
    'DGS10': '10-Year Treasury Rate',
    'DGS20': '20-Year Treasury Rate',
    'DGS30': '30-Year Treasury Rate',
    'T10Y2Y': '10-Year Treasury Constant Maturity Minus 2-Year Treasury',
    'T10Y3M': '10-Year Treasury Constant Maturity Minus 3-Month Treasury',
    'DFEDTARU': 'Federal Funds Target Rate Upper Limit',
    'DFEDTARL': 'Federal Funds Target Rate Lower Limit',
    'DFEDTAR': 'Federal Funds Target Rate',
    'UNRATE': 'Unemployment Rate',
    'CPIAUCSL': 'Consumer Price Index',
    'GDP': 'Gross Domestic Product',
    'GDPPOT': 'Real Potential GDP',
    'GDPC1': 'Real GDP',
    'INDPRO': 'Industrial Production Index',
    'PAYEMS': 'All Employees, Total Nonfarm',
    'UNEMPLOY': 'Unemployed',
    'CIVPART': 'Civilian Labor Force Participation Rate',
    'EMRATIO': 'Employment-Population Ratio'
}

def download_fred_series(series_id, series_name, start_date='2005-01-01', end_date=None):
    """
    Baixar série específica do FRED
    """
    print(f"📊 Baixando {series_name} ({series_id})...")
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'frequency': 'm',  # Monthly
        'units': 'lin'  # Levels
    }
    
    try:
        response = requests.get(f"{FRED_BASE_URL}/series/observations", params=params)
        response.raise_for_status()
        
        data = response.json()
        observations = data['observations']
        
        if not observations:
            print(f"   ⚠️  Nenhum dado disponível para {series_name}")
            return None
        
        # Converter para DataFrame
        series_data = []
        for obs in observations:
            if obs['value'] != '.':
                try:
                    series_data.append({
                        'date': pd.to_datetime(obs['date']),
                        series_id.lower(): float(obs['value'])
                    })
                except ValueError:
                    continue
        
        if not series_data:
            print(f"   ⚠️  Nenhum dado válido para {series_name}")
            return None
        
        df = pd.DataFrame(series_data)
        df.set_index('date', inplace=True)
        
        print(f"   ✅ {series_name}: {len(df)} observações")
        print(f"      Período: {df.index[0].date()} a {df.index[-1].date()}")
        print(f"      Valor médio: {df.iloc[:, 0].mean():.4f}")
        print(f"      Valor atual: {df.iloc[-1, 0]:.4f}")
        
        return df
        
    except Exception as e:
        print(f"   ❌ Erro ao baixar {series_name}: {e}")
        return None

def download_all_fed_series(start_date='2005-01-01', end_date=None):
    """
    Baixar todas as séries do Fed
    """
    print("🚀 DOWNLOAD COMPLETO DE DADOS DO FED")
    print("=" * 60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"API Key: {FRED_API_KEY[:8]}...")
    print(f"Período: {start_date} a {end_date or 'hoje'}")
    print("=" * 60)
    
    all_data = {}
    successful_downloads = 0
    failed_downloads = 0
    
    for series_id, series_name in FED_SERIES.items():
        df = download_fred_series(series_id, series_name, start_date, end_date)
        
        if df is not None:
            all_data[series_id] = df
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    print(f"\n📊 RESUMO DO DOWNLOAD:")
    print(f"   ✅ Sucessos: {successful_downloads}")
    print(f"   ❌ Falhas: {failed_downloads}")
    print(f"   📈 Total de séries: {len(FED_SERIES)}")
    
    return all_data

def combine_fed_data(all_data):
    """
    Combinar todos os dados do Fed em um DataFrame
    """
    print("\n🔄 Combinando dados do Fed...")
    
    if not all_data:
        print("❌ Nenhum dado para combinar")
        return None
    
    # Combinar todos os DataFrames
    combined = pd.concat(list(all_data.values()), axis=1, join='outer')
    
    # Remover colunas duplicadas (se houver)
    combined = combined.loc[:, ~combined.columns.duplicated()]
    
    # Ordenar por data
    combined = combined.sort_index()
    
    print(f"✅ Dados combinados: {len(combined)} observações")
    print(f"   Período: {combined.index[0].date()} a {combined.index[-1].date()}")
    print(f"   Colunas: {len(combined.columns)}")
    print(f"   Colunas: {list(combined.columns)}")
    
    return combined

def add_derived_variables(df):
    """
    Adicionar variáveis derivadas
    """
    print("\n📈 Adicionando variáveis derivadas...")
    
    # Taxa de juros principal (Federal Funds Rate)
    if 'fedfunds' in df.columns:
        df['fed_rate'] = df['fedfunds']
    elif 'dff' in df.columns:
        df['fed_rate'] = df['dff']
    
    # Mudanças nas taxas
    rate_columns = [col for col in df.columns if any(rate in col.lower() for rate in ['fed', 'dgs', 'dfed'])]
    
    for col in rate_columns:
        if col in df.columns:
            df[f'{col}_change'] = df[col].diff()
            df[f'{col}_pct_change'] = df[col].pct_change() * 100
    
    # Yield curve spreads
    if 'dgs10' in df.columns and 'dgs2' in df.columns:
        df['yield_curve_10y2y'] = df['dgs10'] - df['dgs2']
    
    if 'dgs10' in df.columns and 'dgs3mo' in df.columns:
        df['yield_curve_10y3m'] = df['dgs10'] - df['dgs3mo']
    
    # Inflação (se CPI disponível)
    if 'cpiausl' in df.columns:
        df['inflation_yoy'] = df['cpiausl'].pct_change(12) * 100
        df['inflation_mom'] = df['cpiausl'].pct_change() * 100
    
    # PIB (se disponível)
    if 'gdp' in df.columns:
        df['gdp_growth_yoy'] = df['gdp'].pct_change(4) * 100
        df['gdp_growth_qoq'] = df['gdp'].pct_change() * 100
    
    print(f"✅ Variáveis derivadas adicionadas")
    print(f"   Total de colunas: {len(df.columns)}")
    
    return df

def save_fed_data(df, metadata):
    """
    Salvar dados do Fed
    """
    print("\n💾 Salvando dados do Fed...")
    
    # Criar diretórios
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Salvar dados brutos
    df.to_csv('data/raw/fed_detailed_data.csv')
    print("✅ CSV salvo: data/raw/fed_detailed_data.csv")
    
    # Salvar JSON com metadados
    json_data = {
        'metadata': metadata,
        'data': df.to_dict('records')
    }
    
    with open('data/raw/fed_detailed_data.json', 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    print("✅ JSON salvo: data/raw/fed_detailed_data.json")
    
    # Salvar dados processados (sem NaNs)
    df_clean = df.dropna()
    df_clean.to_csv('data/processed/fed_clean_data.csv')
    print("✅ Dados limpos salvos: data/processed/fed_clean_data.csv")
    
    return df

def main():
    """
    Função principal
    """
    # Definir período
    start_date = '2005-01-01'
    end_date = '2025-12-31'
    
    # Baixar todas as séries
    all_data = download_all_fed_series(start_date, end_date)
    
    if not all_data:
        print("❌ Erro: Nenhum dado foi baixado")
        return
    
    # Combinar dados
    combined_df = combine_fed_data(all_data)
    
    if combined_df is None:
        print("❌ Erro: Não foi possível combinar os dados")
        return
    
    # Adicionar variáveis derivadas
    combined_df = add_derived_variables(combined_df)
    
    # Metadados
    metadata = {
        'created_at': datetime.now().isoformat(),
        'observations': len(combined_df),
        'start_date': combined_df.index[0].isoformat(),
        'end_date': combined_df.index[-1].isoformat(),
        'columns': list(combined_df.columns),
        'source': 'FRED API',
        'api_key': FRED_API_KEY[:8] + '...',
        'series_count': len(all_data)
    }
    
    # Salvar dados
    save_fed_data(combined_df, metadata)
    
    print("\n🎉 DOWNLOAD DO FED CONCLUÍDO COM SUCESSO!")
    print(f"📊 Total de observações: {len(combined_df)}")
    print(f"📅 Período: {combined_df.index[0].date()} a {combined_df.index[-1].date()}")
    print(f"📈 Total de séries: {len(combined_df.columns)}")
    print(f"💾 Arquivos salvos em: data/raw/ e data/processed/")

if __name__ == "__main__":
    main()
