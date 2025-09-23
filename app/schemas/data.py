"""
Schemas Pydantic para dados
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class DataCollectionResponse(BaseModel):
    """Resposta da coleta de dados"""
    status: str
    message: str
    total_records: int
    sources: Dict[str, Any]
    collected_at: datetime


class SeriesDataResponse(BaseModel):
    """Resposta de dados de série temporal"""
    id: int
    series_code: str
    series_name: str
    source: str
    country: Optional[str]
    date: datetime
    value: float
    unit: Optional[str]
    frequency: Optional[str]
    last_updated: datetime


class CollectionLogResponse(BaseModel):
    """Resposta do log de coleta"""
    id: int
    source: str
    series_code: str
    status: str
    records_collected: int
    error_message: Optional[str]
    execution_time: Optional[float]
    collected_at: datetime
