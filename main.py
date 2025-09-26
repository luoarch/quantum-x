#!/usr/bin/env python3
"""
Sistema de Análise de Spillovers Econômicos Brasil-Mundo
Fase 1: VAR + Neural Enhancement com Validação Científica

Este script demonstra o funcionamento básico do sistema.
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_loader import load_data
from src.models.hybrid_model import create_hybrid_model
from src.models.baseline_model import BaselineVARModel
from src.validation.scientific_validation import ScientificValidator
import pandas as pd
import numpy as np

def main():
    """Função principal do sistema"""
    print("🚀 Sistema de Análise de Spillovers Econômicos Brasil-Mundo")
    print("=" * 60)
    print("Fase 1: VAR + Neural Enhancement com Validação Científica")
    print("=" * 60)
    
    try:
        # 1. Carregar dados
        print("\n📊 1. Carregando dados econômicos...")
        data = load_data()
        print(f"✅ Dados carregados: {len(data)} observações")
        print(f"   Período: {data.index[0].date()} a {data.index[-1].date()}")
        
        # 2. Treinar modelo baseline
        print("\n📊 2. Treinando modelo baseline VAR...")
        baseline_model = BaselineVARModel()
        baseline_model.fit(data)
        print("✅ Modelo baseline treinado com sucesso!")
        
        # 3. Criar e treinar modelo híbrido
        print("\n🧠 3. Treinando modelo híbrido VAR + Neural Network...")
        model = create_hybrid_model(
            var_lags=12,
            nn_hidden_layers=(50, 25),
            simple_weight=0.4,
            complex_weight=0.6
        )
        
        model.fit(data)
        print("✅ Modelo híbrido treinado com sucesso!")
        
        # 4. Validação científica
        print("\n🔬 4. Executando validação científica...")
        validator = ScientificValidator()
        validation_results = validator.comprehensive_validation(model, data, baseline_model)
        
        # 5. Gerar relatório de validação
        print("\n📋 5. Gerando relatório de validação...")
        validation_report = validator.generate_validation_report(model, data)
        print(validation_report)
        
        # 6. Demonstração de predições
        print("\n🔮 6. Demonstração de predições...")
        demo_predictions(data, model)
        
        # 7. Análise de spillovers
        print("\n📈 7. Análise de spillovers...")
        analyze_spillovers(data, model)
        
        print("\n🎉 Sistema executado com sucesso!")
        print("✅ Fase 1 implementada e funcionando")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def demo_predictions(data: pd.DataFrame, model):
    """Demonstrar predições do modelo com contexto histórico"""
    print("   Demonstração de predições com incerteza:")
    
    # Usar últimos 12 períodos como contexto histórico
    historical_context = data[['fed_rate', 'selic']].tail(12)
    
    for i in range(5):
        try:
            # Construir input com contexto histórico
            X_new = historical_context.iloc[-1:].values  # Última observação
            
            # Simular próximo período (para demo realística)
            np.random.seed(42 + i)  # Para reprodutibilidade
            fed_simulation = X_new[0,0] + np.random.normal(0, 0.1)
            selic_simulation = X_new[0,1] + np.random.normal(0, 0.2)
            X_future = np.array([[fed_simulation, selic_simulation]])
            
            # Fazer predição (converter array para DataFrame)
            X_future_df = pd.DataFrame(X_future, columns=['fed_rate', 'selic'])
            prediction = model.predict_with_uncertainty(X_future_df)
            
            # ACESSAR VALORES DIRETAMENTE (não indexar arrays)
            spillover_val = prediction['prediction']
            uncertainty_val = prediction['uncertainty']
            is_outlier_val = prediction['is_outlier']
            high_uncertainty_val = prediction['high_uncertainty']
            
            # Calcular data futura para demonstração
            future_month = 10 + i
            future_year = 2025 if future_month <= 12 else 2026
            future_month = future_month if future_month <= 12 else future_month - 12
            
            print(f"   Período {i+1} ({future_year}-{future_month:02d}):")
            print(f"     Fed Rate: {fed_simulation:.2f}%")
            print(f"     Selic: {selic_simulation:.2f}%")
            print(f"     Predição Spillover: {spillover_val:.4f}")
            print(f"     Incerteza: {uncertainty_val:.4f}")
            print(f"     É Outlier: {'Sim' if is_outlier_val else 'Não'}")
            print(f"     Alta Incerteza: {'Sim' if high_uncertainty_val else 'Não'}")
            print()
            
        except Exception as e:
            print(f"❌ Erro no período {i+1}: {e}")
            import traceback
            traceback.print_exc()
            break

def analyze_spillovers(data: pd.DataFrame, model):
    """Analisar padrões de spillovers"""
    print("   Análise de padrões de spillovers:")
    
    # Calcular spillovers históricos
    if 'spillover' in data.columns:
        spillover_mean = data['spillover'].mean()
        spillover_std = data['spillover'].std()
        spillover_corr = data['fed_rate'].corr(data['selic'])
        
        print(f"   Spillover médio histórico: {spillover_mean:.4f}")
        print(f"   Desvio padrão: {spillover_std:.4f}")
        print(f"   Correlação Fed-Selic: {spillover_corr:.3f}")
        
        # Análise por períodos
        recent_data = data.tail(24)  # Últimos 2 anos
        recent_spillover = recent_data['spillover'].mean()
        print(f"   Spillover recente (24 meses): {recent_spillover:.4f}")
        
        # Detectar períodos de alta volatilidade
        high_vol_periods = data[abs(data['spillover']) > spillover_std * 2]
        if len(high_vol_periods) > 0:
            print(f"   Períodos de alta volatilidade: {len(high_vol_periods)}")
            print(f"   Último período de alta volatilidade: {high_vol_periods.index[-1].strftime('%Y-%m')}")

def print_system_info():
    """Imprimir informações do sistema"""
    print("\n📋 Informações do Sistema:")
    print(f"   Python: {sys.version}")
    print(f"   Pandas: {pd.__version__}")
    print(f"   NumPy: {np.__version__}")
    print(f"   Diretório: {os.getcwd()}")

if __name__ == "__main__":
    print_system_info()
    exit_code = main()
    sys.exit(exit_code)
