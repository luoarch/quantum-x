"""
Endpoint de teste para o dashboard
"""

from fastapi import APIRouter
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test")
async def test_endpoint() -> Dict[str, Any]:
    """Endpoint de teste para verificar se a API está funcionando"""
    logger.info("🧪 Endpoint de teste chamado")
    
    return {
        "status": "success",
        "message": "API funcionando corretamente",
        "data": {
            "test": True,
            "timestamp": "2025-09-23T22:00:00Z"
        }
    }

@router.get("/dashboard-data")
async def get_dashboard_data() -> Dict[str, Any]:
    """Endpoint específico para o dashboard com dados formatados"""
    logger.info("📊 Buscando dados para o dashboard")
    
    # Dados de exemplo para o dashboard
    return {
        "currentSignal": {
            "date": "2025-09-23T22:00:00Z",
            "signal": "HOLD",
            "strength": 75,
            "confidence": 85.5,
            "regime": "EXPANSION",
            "buyProbability": 25.0,
            "sellProbability": 15.0
        },
        "recentSignals": [
            {
                "date": "2025-09-23T21:00:00Z",
                "signal": "HOLD",
                "confidence": 85.5
            },
            {
                "date": "2025-09-23T20:00:00Z", 
                "signal": "HOLD",
                "confidence": 82.3
            }
        ],
        "cliData": [
            {"date": "2025-09-23", "value": 100.5, "confidence": 85.5},
            {"date": "2025-09-22", "value": 100.2, "confidence": 82.3},
            {"date": "2025-09-21", "value": 99.8, "confidence": 80.1}
        ],
        "performance": {
            "totalSignals": 18,
            "buySignals": 0,
            "sellSignals": 0,
            "holdSignals": 18,
            "avgConfidence": 85.5,
            "avgBuyProbability": 25.0,
            "avgSellProbability": 15.0,
            "regimeSummary": [
                {"regime": "EXPANSION", "probability": 45.0, "frequency": 38.9},
                {"regime": "CONTRACTION", "probability": 35.0, "frequency": 38.9},
                {"regime": "RECOVERY", "probability": 20.0, "frequency": 16.7},
                {"regime": "RECESSION", "probability": 5.0, "frequency": 5.6}
            ],
            "hrpAllocation": [
                {"asset": "TESOURO_IPCA", "allocation": 50.0},
                {"asset": "BOVA11", "allocation": 50.0}
            ],
            "hrpMetrics": {
                "expectedReturn": 2.44,
                "volatility": 0.45,
                "sharpeRatio": 5.28,
                "effectiveDiversification": 2.0
            }
        },
        "assets": [
            {
                "ticker": "TESOURO_IPCA",
                "name": "Tesouro IPCA+ 2045",
                "price": 100.0,
                "change": 0.5,
                "changePercent": 0.5,
                "allocation": 50.0
            },
            {
                "ticker": "BOVA11", 
                "name": "BOVA11",
                "price": 100.0,
                "change": -0.2,
                "changePercent": -0.2,
                "allocation": 50.0
            }
        ],
        "lastUpdate": "2025-09-23T22:00:00Z"
    }
