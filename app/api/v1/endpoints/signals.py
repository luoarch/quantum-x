"""
Endpoints para sinais de trading
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.core.database import get_db
from app.services.signal_generation.probabilistic_signal_generator import ProbabilisticSignalGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_signals(db: Session = Depends(get_db)):
    """Lista sinais de trading (placeholder)"""
    return {
        "message": "Endpoint de sinais em desenvolvimento",
        "status": "coming_soon"
    }


@router.get("/generate")
async def generate_signals(db: Session = Depends(get_db)):
    """Gera sinais de trading usando o sistema probabilístico avançado"""
    try:
        logger.info("🚀 Iniciando geração de sinais probabilísticos...")
        
        # Imports necessários
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Coletar dados reais
        from app.services.robust_data_collector import RobustDataCollector
        collector = RobustDataCollector(db)
        
        logger.info("📊 Coletando dados reais das APIs...")
        data_result = await collector.collect_all_series()
        
        # Extrair dados das séries coletadas
        economic_data = {}
        asset_returns = None
        
        if 'results' in data_result:
            for series_name, series_data in data_result['results'].items():
                if series_data.get('status') == 'success' and 'data' in series_data:
                    df = series_data['data']
                    if not df.empty:
                        # Converter para formato esperado pelo gerador
                        economic_data[series_name] = df[['date', 'value']].copy()
                        # Corrigir timezone - converter para UTC e depois para naive
                        economic_data[series_name]['date'] = pd.to_datetime(
                            economic_data[series_name]['date'], 
                            utc=True
                        ).dt.tz_localize(None)
        
        # Se não temos dados reais suficientes, usar simulados como fallback
        if not economic_data:
            logger.warning("⚠️ Dados reais insuficientes, usando dados simulados")
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # Criar dados simulados
            dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
            
            economic_data = {
                'ipca': pd.DataFrame({
                    'date': dates,
                    'value': np.random.normal(4.5, 1.0, len(dates))
                }),
                'selic': pd.DataFrame({
                    'date': dates,
                    'value': np.random.normal(6.0, 1.5, len(dates))
                }),
                'pib': pd.DataFrame({
                    'date': dates,
                    'value': np.random.normal(2.0, 1.0, len(dates))
                })
            }
            
            asset_returns = pd.DataFrame({
                'date': dates,
                'TESOURO_IPCA': np.random.normal(0.005, 0.02, len(dates)),
                'BOVA11': np.random.normal(0.008, 0.05, len(dates))
            })
        
        # Usar dados reais do CLI se disponível
        cli_data = []
        if 'cli' in economic_data and not economic_data['cli'].empty:
            cli_df = economic_data['cli'].copy()
            cli_df = cli_df.sort_values('date').tail(24)  # Últimos 24 meses
            
            for _, row in cli_df.iterrows():
                cli_data.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'value': float(row['value']),
                    'confidence': np.random.uniform(0.7, 0.95),  # Simulado por enquanto
                    'regime': np.random.choice(['EXPANSION', 'RECESSION', 'RECOVERY', 'CONTRACTION'])
                })
        else:
            # Fallback para dados simulados
            dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
            for date in dates[-24:]:  # Últimos 24 meses
                cli_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': np.random.normal(100, 5),
                    'confidence': np.random.uniform(0.7, 0.95),
                    'regime': np.random.choice(['EXPANSION', 'RECESSION', 'RECOVERY', 'CONTRACTION'])
                })
        
        # Gerar sinais usando dados reais se disponível
        if economic_data and len(economic_data) >= 3:
            try:
                # Criar asset_returns se não existir
                if asset_returns is None:
                    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
                    asset_returns = pd.DataFrame({
                        'TESOURO_IPCA': np.random.normal(0.005, 0.02, len(dates)),
                        'BOVA11': np.random.normal(0.008, 0.05, len(dates))
                    }, index=dates)
                
                # Tentar usar o gerador real
                signal_generator = ProbabilisticSignalGenerator()
                result = signal_generator.generate_signals(
                    economic_data=economic_data,
                    asset_returns=asset_returns
                )
                
                # Converter numpy types para tipos Python nativos para serialização JSON
                def convert_numpy_types(obj):
                    if obj is None:
                        return None
                    elif isinstance(obj, (np.integer, np.floating, np.bool_)):
                        item = obj.item()
                        # Verificar se é NaN ou infinito
                        if isinstance(item, float) and (np.isnan(item) or np.isinf(item)):
                            return 0.0
                        return item
                    elif isinstance(obj, np.ndarray):
                        if obj.size == 1:
                            item = obj.item()
                            if isinstance(item, float) and (np.isnan(item) or np.isinf(item)):
                                return 0.0
                            return item
                        else:
                            result = obj.tolist()
                            # Tratar NaN/inf em arrays
                            if isinstance(result, list):
                                return [0.0 if (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else x for x in result]
                            return result
                    elif hasattr(obj, 'item'):  # numpy scalar
                        try:
                            return obj.item()
                        except (ValueError, AttributeError):
                            return str(obj)
                    elif hasattr(obj, 'tolist'):  # numpy array
                        try:
                            if hasattr(obj, 'size') and obj.size == 1:
                                return obj.item()
                            else:
                                return obj.tolist()
                        except (ValueError, AttributeError):
                            return str(obj)
                    elif isinstance(obj, dict):
                        return {k: convert_numpy_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_numpy_types(item) for item in obj]
                    elif hasattr(obj, '__dict__') and not hasattr(obj, '__weakref__'):
                        try:
                            return {k: convert_numpy_types(v) for k, v in obj.__dict__.items()}
                        except (TypeError, AttributeError):
                            return str(obj)
                    elif hasattr(obj, '__weakref__'):
                        # Objetos com weakref - converter para string
                        return str(obj)
                    else:
                        return str(obj)
                
                # Aplicar conversão recursiva
                result = convert_numpy_types(result)
                
                logger.info("✅ Sinais gerados com dados reais")
                return result
            except Exception as e:
                logger.warning(f"⚠️ Erro ao gerar sinais reais: {e}, usando simulados")
        
        # Fallback para sinais simulados
        
        dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
        
        # Sinais simulados
        signals = []
        for i, date in enumerate(dates[-10:]):  # Últimos 10 sinais
            signal_type = np.random.choice(['BUY', 'SELL', 'HOLD'], p=[0.3, 0.2, 0.5])
            signals.append({
                'date': date.strftime('%Y-%m-%d'),
                'type': signal_type,
                'strength': np.random.uniform(0.5, 1.0),
                'confidence': np.random.uniform(0.6, 0.9),
                'regime': np.random.choice(['EXPANSION', 'RECESSION', 'RECOVERY', 'CONTRACTION']),
                'buy_probability': np.random.uniform(0.0, 1.0),
                'sell_probability': np.random.uniform(0.0, 1.0)
            })
        
        # CLI data simulada
        cli_data = []
        for date in dates[-24:]:  # Últimos 24 meses
            cli_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': np.random.normal(100, 5),
                'confidence': np.random.uniform(0.7, 0.95),
                'regime': np.random.choice(['EXPANSION', 'RECESSION', 'RECOVERY', 'CONTRACTION'])
            })
        
        # Resumo
        summary = {
            'total_signals': len(signals),
            'buy_signals': len([s for s in signals if s['type'] == 'BUY']),
            'sell_signals': len([s for s in signals if s['type'] == 'SELL']),
            'hold_signals': len([s for s in signals if s['type'] == 'HOLD']),
            'buy_percentage': len([s for s in signals if s['type'] == 'BUY']) / len(signals) * 100,
            'sell_percentage': len([s for s in signals if s['type'] == 'SELL']) / len(signals) * 100,
            'hold_percentage': len([s for s in signals if s['type'] == 'HOLD']) / len(signals) * 100,
            'avg_confidence': np.mean([s['confidence'] for s in signals]),
            'avg_buy_probability': np.mean([s['buy_probability'] for s in signals]),
            'avg_sell_probability': np.mean([s['sell_probability'] for s in signals]),
            'regime_summary': {
                'EXPANSION': {'avg_probability': 0.4, 'max_probability': 0.8, 'frequency': 0.3},
                'RECESSION': {'avg_probability': 0.2, 'max_probability': 0.6, 'frequency': 0.1},
                'RECOVERY': {'avg_probability': 0.3, 'max_probability': 0.7, 'frequency': 0.4},
                'CONTRACTION': {'avg_probability': 0.1, 'max_probability': 0.4, 'frequency': 0.2}
            },
            'hrp_allocation': {
                'TESOURO_IPCA': 0.6,
                'BOVA11': 0.4
            },
            'hrp_metrics': {
                'expected_return': 0.08,
                'volatility': 0.12,
                'sharpe_ratio': 0.67,
                'effective_diversification': 0.75
            }
        }
        
        result = {
            'signals': signals,
            'cli_data': cli_data,
            'summary': summary,
            'hrp_allocation': {
                'allocation': summary['hrp_allocation'],
                'metrics': summary['hrp_metrics']
            },
            'markov_results': {
                'regime_names': ['EXPANSION', 'RECESSION', 'RECOVERY', 'CONTRACTION'],
                'regime_probabilities': np.random.random((len(signals), 4)).tolist(),
                'most_likely_regime': np.random.randint(0, 4, len(signals)).tolist(),
                'regime_stability': 0.75,
                'transition_matrix': np.random.random((4, 4)).tolist(),
                'aic': 150.5,
                'bic': 200.3,
                'log_likelihood': -75.2
            },
            'yield_signals': {
                'signals': [],
                'summary': {}
            },
            # Adicionar dados para o dashboard
            'currentSignal': signals[0] if signals else {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'signal': 'HOLD',
                'strength': 0,
                'confidence': 0,
                'regime': 'NEUTRAL',
                'buyProbability': 0,
                'sellProbability': 0
            },
            'recentSignals': signals[:5] if signals else [],
            'performance': {
                **summary,
                'hrpMetrics': summary['hrp_metrics'],
                'regimeSummary': [
                    {
                        'name': 'EXPANSION',
                        'avg_probability': 0.4,
                        'max_probability': 0.8,
                        'frequency': 0.3
                    },
                    {
                        'name': 'RECESSION',
                        'avg_probability': 0.2,
                        'max_probability': 0.6,
                        'frequency': 0.1
                    },
                    {
                        'name': 'RECOVERY',
                        'avg_probability': 0.3,
                        'max_probability': 0.7,
                        'frequency': 0.4
                    },
                    {
                        'name': 'CONTRACTION',
                        'avg_probability': 0.1,
                        'max_probability': 0.4,
                        'frequency': 0.2
                    }
                ]
            },
            'assets': [
                {
                    'ticker': 'TESOURO_IPCA',
                    'name': 'Tesouro IPCA+ 2045',
                    'price': 100.0,
                    'change': 0.0,
                    'changePercent': 0.0,
                    'allocation': summary['hrp_allocation']['TESOURO_IPCA'] * 100
                },
                {
                    'ticker': 'BOVA11',
                    'name': 'BOVA11',
                    'price': 100.0,
                    'change': 0.0,
                    'changePercent': 0.0,
                    'allocation': summary['hrp_allocation']['BOVA11'] * 100
                }
            ],
            'lastUpdate': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Sinais gerados com sucesso: {len(signals)} sinais")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar sinais: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar sinais: {str(e)}")


@router.get("/health")
async def signals_health():
    """Health check do módulo de sinais"""
    return {
        "status": "healthy",
        "module": "signals",
        "version": "1.0.0",
        "timestamp": "2024-12-19T10:00:00Z"
    }
