#!/usr/bin/env python3
"""
Pipeline de Treino End-to-End para Modelos FED-Selic
Sprint 1 - Tarefa 1.1

Este script implementa o pipeline completo de treino:
- Ingestão de dados
- Hash SHA256 do dataset
- Preparação de features
- Treino de LP e BVAR
- Cálculo de IRFs
- Materialização de artefatos
- Geração de metadata.json
"""

import argparse
import json
import pickle
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import sys

import numpy as np
import pandas as pd

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.local_projections import LocalProjectionsForecaster
from src.models.bvar_minnesota import BVARMinnesota


class TrainingPipeline:
    """Pipeline completo de treino de modelos FED-Selic"""
    
    def __init__(self, version: str, output_dir: str = "data/models"):
        self.version = version
        self.output_dir = Path(output_dir)
        self.version_dir = self.output_dir / version
        
        # Criar diretórios
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadados
        self.metadata: Dict[str, Any] = {
            "version": version,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "data_hash": None,
            "methodology": "LP primary, BVAR fallback",
            "n_observations": 0,
            "models": {}
        }
        
        print(f"🚀 Iniciando pipeline de treino versão {version}")
        print(f"📁 Diretório de saída: {self.version_dir}")
    
    def load_data(self, data_path: str = "data/raw/fed_selic_combined.csv") -> pd.DataFrame:
        """Carregar dados brutos"""
        print(f"\n📊 Carregando dados de {data_path}...")
        
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Arquivo de dados não encontrado: {data_path}")
        
        df = pd.read_csv(data_file, index_col=0)
        
        # Renomear index para 'date' se necessário
        df.index.name = 'date'
        df = df.reset_index()
        
        print(f"✅ Dados carregados: {len(df)} observações")
        print(f"   Colunas: {list(df.columns)}")
        
        return df
    
    def hash_dataset(self, df: pd.DataFrame) -> str:
        """Calcular hash SHA256 do dataset"""
        print("\n🔐 Calculando hash do dataset...")
        
        # Converter DataFrame para bytes reproduzíveis
        # Ordenar por índice para garantir ordem consistente
        df_sorted = df.sort_index()
        
        # Converter para CSV string
        csv_string = df_sorted.to_csv(index=False)
        
        # Calcular SHA256
        hash_obj = hashlib.sha256(csv_string.encode('utf-8'))
        data_hash = f"sha256:{hash_obj.hexdigest()}"
        
        print(f"✅ Hash calculado: {data_hash[:64]}...")
        return data_hash
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.DatetimeIndex, pd.DatetimeIndex]:
        """Preparar features para treino"""
        print("\n🔧 Preparando features...")
        
        # Normalizar nomes de colunas
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
        if 'fed_funds_rate' in df.columns:
            df.rename(columns={'fed_funds_rate': 'fed_rate'}, inplace=True)
        if 'selic' in df.columns and 'selic_rate' not in df.columns:
            df.rename(columns={'selic': 'selic_rate'}, inplace=True)
        
        # Verificar colunas necessárias
        required_cols = ['date', 'fed_rate', 'selic_rate']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Colunas faltando: {missing_cols}. Disponíveis: {list(df.columns)}")
        
        # Converter datas
        df['date'] = pd.to_datetime(df['date'])
        
        # Calcular diferenças (movimentos em bps)
        df['fed_move'] = df['fed_rate'].diff() * 100  # converter para bps
        df['selic_move'] = df['selic_rate'].diff() * 100  # converter para bps
        
        # Remover NaNs
        df = df.dropna()
        
        # Extrair séries
        fed_moves = df['fed_move']
        selic_moves = df['selic_move']
        dates = pd.DatetimeIndex(df['date'])
        
        self.metadata['n_observations'] = len(df)
        
        print(f"✅ Features preparadas:")
        print(f"   Observações: {len(df)}")
        print(f"   Período: {dates.min().date()} até {dates.max().date()}")
        print(f"   Fed move: média={fed_moves.mean():.2f} bps, std={fed_moves.std():.2f} bps")
        print(f"   Selic move: média={selic_moves.mean():.2f} bps, std={selic_moves.std():.2f} bps")
        
        return fed_moves, selic_moves, dates, dates
    
    def train_local_projections(
        self, 
        fed_moves: pd.Series, 
        selic_moves: pd.Series, 
        dates: pd.DatetimeIndex
    ) -> LocalProjectionsForecaster:
        """Treinar modelo Local Projections"""
        print("\n🔬 Treinando Local Projections...")
        
        # Criar modelo
        lp = LocalProjectionsForecaster(
            max_horizon=12,
            max_lags=4,
            alpha=0.1,
            regularization='ridge',
            significance_level=0.05
        )
        
        # Preparar dados
        df_prepared = lp.prepare_data(
            fed_data=fed_moves,
            selic_data=selic_moves,
            fed_dates=dates,
            selic_dates=dates
        )
        
        # Treinar
        results = lp.fit(df_prepared)
        
        # Avaliar
        evaluation = lp.evaluate_model()
        
        # Armazenar metadata
        self.metadata['models']['local_projections'] = {
            'n_horizons': evaluation['n_horizons'],
            'avg_r_squared': float(evaluation['avg_r_squared']),
            'avg_irf': float(evaluation['avg_irf']),
            'max_irf': float(evaluation['max_irf']),
            'horizon_max_response': evaluation['horizon_max_response']
        }
        
        print(f"✅ Local Projections treinado:")
        print(f"   Horizontes: {evaluation['n_horizons']}")
        print(f"   R² médio: {evaluation['avg_r_squared']:.3f}")
        print(f"   IRF médio: {evaluation['avg_irf']:.3f}")
        print(f"   Máxima resposta: {evaluation['horizon_max_response']}")
        
        return lp
    
    def train_bvar(
        self, 
        fed_moves: pd.Series, 
        selic_moves: pd.Series, 
        dates: pd.DatetimeIndex
    ) -> BVARMinnesota:
        """Treinar modelo BVAR Minnesota"""
        print("\n🔬 Treinando BVAR Minnesota...")
        
        # Criar modelo
        bvar = BVARMinnesota(
            n_lags=2,
            n_vars=2,
            minnesota_params={
                'lambda1': 0.1,
                'lambda2': 0.5,
                'lambda3': 1.0,
                'lambda4': 0.1,
                'mu': 0.0,
                'sigma': 1.0
            },
            n_simulations=1000
        )
        
        # Preparar dados
        Y, X = bvar.prepare_data(
            fed_data=fed_moves,
            selic_data=selic_moves,
            fed_dates=dates,
            selic_dates=dates
        )
        
        # Treinar
        results = bvar.estimate()
        
        # Avaliar
        evaluation = bvar.evaluate_model()
        
        # Armazenar metadata
        self.metadata['models']['bvar_minnesota'] = {
            'n_vars': bvar.n_vars,
            'n_lags': bvar.n_lags,
            'n_obs': results['n_obs'],
            'r_squared': float(np.mean(evaluation['r_squared'])),
            'model_quality': evaluation['model_quality'],
            'irf_summary': {
                'max_response': float(evaluation['irf_summary']['max_response']),
                'horizon_max_response': int(evaluation['irf_summary']['horizon_max_response']),
                'persistence': float(evaluation['irf_summary']['persistence'])
            }
        }
        
        print(f"✅ BVAR Minnesota treinado:")
        print(f"   Observações: {results['n_obs']}")
        print(f"   R² médio: {np.mean(evaluation['r_squared']):.3f}")
        print(f"   Qualidade: {evaluation['model_quality']}")
        
        return bvar
    
    def save_artifacts(
        self, 
        lp_model: LocalProjectionsForecaster, 
        bvar_model: BVARMinnesota
    ):
        """Salvar artefatos do modelo"""
        print("\n💾 Salvando artefatos...")
        
        # Salvar modelo LP
        lp_path = self.version_dir / "model_lp.pkl"
        with open(lp_path, 'wb') as f:
            pickle.dump(lp_model, f)
        print(f"✅ Salvo: {lp_path}")
        
        # Salvar modelo BVAR
        bvar_path = self.version_dir / "model_bvar.pkl"
        with open(bvar_path, 'wb') as f:
            pickle.dump(bvar_model, f)
        print(f"✅ Salvo: {bvar_path}")
        
        # Salvar IRFs do LP
        lp_irfs = lp_model.get_impulse_response_function()
        irfs_path = self.version_dir / "irfs_lp.json"
        
        # Converter para formato serializável
        irfs_serializable = {}
        for horizon, values in lp_irfs.items():
            irfs_serializable[horizon] = {
                'irf': float(values['irf']),
                'ci_lower': float(values['ci_lower']),
                'ci_upper': float(values['ci_upper'])
            }
        
        with open(irfs_path, 'w') as f:
            json.dump(irfs_serializable, f, indent=2)
        print(f"✅ Salvo: {irfs_path}")
        
        # Salvar IRFs do BVAR
        bvar_irf_summary = bvar_model.get_irf_summary()
        bvar_irfs_path = self.version_dir / "irfs_bvar.json"
        
        # Converter IRF values para formato serializável
        irf_values_serializable = {
            k: float(v) for k, v in bvar_irf_summary['irf_values'].items()
        }
        
        bvar_irf_serializable = {
            'max_response': float(bvar_irf_summary['max_response']),
            'horizon_max_response': int(bvar_irf_summary['horizon_max_response']),
            'persistence': float(bvar_irf_summary['persistence']),
            'irf_values': irf_values_serializable
        }
        
        with open(bvar_irfs_path, 'w') as f:
            json.dump(bvar_irf_serializable, f, indent=2)
        print(f"✅ Salvo: {bvar_irfs_path}")
    
    def save_metadata(self):
        """Salvar metadata.json"""
        print("\n📝 Salvando metadata...")
        
        metadata_path = self.version_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"✅ Salvo: {metadata_path}")
        print(f"\n📊 Resumo do metadata:")
        print(f"   Versão: {self.metadata['version']}")
        print(f"   Data: {self.metadata['created_at']}")
        print(f"   Hash: {self.metadata['data_hash'][:64]}...")
        print(f"   Observações: {self.metadata['n_observations']}")
    
    def run(self, data_path: str = "data/raw/fed_selic_combined.csv"):
        """Executar pipeline completo"""
        try:
            # 1. Carregar dados
            df = self.load_data(data_path)
            
            # 2. Hash do dataset
            self.metadata['data_hash'] = self.hash_dataset(df)
            
            # 3. Preparar features
            fed_moves, selic_moves, fed_dates, selic_dates = self.prepare_features(df)
            
            # 4. Treinar Local Projections
            lp_model = self.train_local_projections(fed_moves, selic_moves, fed_dates)
            
            # 5. Treinar BVAR
            bvar_model = self.train_bvar(fed_moves, selic_moves, fed_dates)
            
            # 6. Salvar artefatos
            self.save_artifacts(lp_model, bvar_model)
            
            # 7. Salvar metadata
            self.save_metadata()
            
            print("\n" + "="*70)
            print("🎉 PIPELINE COMPLETO COM SUCESSO!")
            print("="*70)
            print(f"\n📦 Artefatos disponíveis em: {self.version_dir}")
            print(f"   - model_lp.pkl")
            print(f"   - model_bvar.pkl")
            print(f"   - irfs_lp.json")
            print(f"   - irfs_bvar.json")
            print(f"   - metadata.json")
            print("\n✅ Modelos prontos para uso na API!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO no pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Pipeline de treino de modelos FED-Selic"
    )
    parser.add_argument(
        '--version',
        type=str,
        required=True,
        help='Versão do modelo (ex: v1.0.0)'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/raw/fed_selic_combined.csv',
        help='Caminho para os dados'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/models',
        help='Diretório de saída para artefatos'
    )
    
    args = parser.parse_args()
    
    # Criar e executar pipeline
    pipeline = TrainingPipeline(
        version=args.version,
        output_dir=args.output_dir
    )
    
    success = pipeline.run(data_path=args.data)
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

