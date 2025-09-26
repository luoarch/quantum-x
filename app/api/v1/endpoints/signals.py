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
    """Gera sinais de trading usando o sistema probabilístico avançado (sem mocks)."""
    try:
        logger.info("🚀 Iniciando geração de sinais probabilísticos (dados reais)...")

        import pandas as pd
        from datetime import datetime

        # Coletar dados reais
        from app.services.robust_data_collector import RobustDataCollector
        collector = RobustDataCollector(db)

        logger.info("📊 Coletando dados reais das APIs...")
        series_dict = await collector.collect_all_series(months=120)

        # Converter para formato esperado pelo gerador: DataFrames indexados por data e coluna 'value'
        economic_data: Dict[str, pd.DataFrame] = {}
        for series_name, df in series_dict.items():
            if hasattr(df, 'empty') and not df.empty and 'date' in df.columns and 'value' in df.columns:
                tmp = df[['date', 'value']].copy()
                tmp['date'] = pd.to_datetime(tmp['date'], errors='coerce')
                tmp = tmp.dropna(subset=['date']).set_index('date').sort_index()
                economic_data[series_name] = tmp

        if len(economic_data) < 2:
            raise HTTPException(status_code=422, detail="Dados reais insuficientes para gerar sinais")

        # Derivar asset_returns reais (proxy/mercado)
        asset_returns = pd.DataFrame()
        # Renda fixa: SELIC mensal
        if 'selic' in economic_data:
            selic_series = economic_data['selic']['value'] / 100.0
            monthly = (1.0 + selic_series) ** (1.0 / 12.0) - 1.0
            asset_returns = pd.DataFrame({'TESOURO_IPCA': monthly}).sort_index()
        # Risco: BOVA11 via Yahoo se disponível
        try:
            yahoo_source = collector.sources.get('yahoo')
            if yahoo_source is not None:
                bova_df = await yahoo_source.fetch_data({'symbol': 'BOVA11', 'period': '3y', 'interval': '1mo'})
                if hasattr(bova_df, 'empty') and not bova_df.empty:
                    tmp = bova_df[['date', 'value']].copy()
                    tmp['date'] = pd.to_datetime(tmp['date'], errors='coerce')
                    tmp = tmp.dropna(subset=['date']).set_index('date').sort_index()
                    bova_rets = tmp['value'].pct_change().fillna(0)
                    if asset_returns.empty:
                        asset_returns = pd.DataFrame(index=bova_rets.index)
                    asset_returns['BOVA11'] = bova_rets
        except Exception as e:
            logger.warning(f"⚠️ Falha ao coletar BOVA11 via Yahoo: {e}")
            # Fallback: proxy de risco via produção industrial
            if 'prod_industrial' in economic_data:
                prod = economic_data['prod_industrial']['value']
                risk_proxy = prod.pct_change().fillna(0)
                if asset_returns.empty:
                    asset_returns = pd.DataFrame(index=risk_proxy.index)
                asset_returns['BOVA11'] = risk_proxy
        asset_returns = asset_returns.sort_index()

        if asset_returns.empty:
            raise HTTPException(status_code=422, detail="Não foi possível derivar asset_returns reais")

        # Gerar sinais
        generator = ProbabilisticSignalGenerator()
        result = generator.generate_signals(economic_data=economic_data, asset_returns=asset_returns)

        # Serialização segura: DataFrames -> records
        def df_to_records(obj: Any) -> Any:
            import pandas as pd  # local import
            if isinstance(obj, pd.DataFrame):
                out = obj.reset_index()
                if 'index' in out.columns:
                    out = out.rename(columns={'index': 'date'})
                # padronizar datas para ISO
                for col in out.columns:
                    if out[col].dtype == 'datetime64[ns]':
                        out[col] = out[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
                return out.to_dict('records')
            if isinstance(obj, dict):
                return {k: df_to_records(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [df_to_records(v) for v in obj]
            return obj

        serialized = df_to_records(result)
        logger.info("✅ Sinais gerados com dados reais")
        return serialized
        
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
