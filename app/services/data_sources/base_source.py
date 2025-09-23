"""
Classe base para fontes de dados
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Classe base abstrata para fontes de dados"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority  # 1 = primária, 2 = secundária, etc.
        self.is_available = True
        self.last_success = None
        self.consecutive_failures = 0
        self.max_failures = 3
        
    @abstractmethod
    async def fetch_data(self, series_config: Dict[str, Any]) -> pd.DataFrame:
        """Busca dados da fonte"""
        pass
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Valida qualidade dos dados"""
        pass
    
    def mark_success(self):
        """Marca sucesso na coleta"""
        self.is_available = True
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        logger.info(f"✅ {self.name}: Coleta bem-sucedida")
    
    def mark_failure(self, error: str):
        """Marca falha na coleta"""
        self.consecutive_failures += 1
        logger.warning(f"❌ {self.name}: Falha #{self.consecutive_failures} - {error}")
        
        if self.consecutive_failures >= self.max_failures:
            self.is_available = False
            logger.error(f"🚫 {self.name}: Fonte desabilitada após {self.max_failures} falhas")
    
    def should_retry(self) -> bool:
        """Verifica se deve tentar novamente"""
        return self.is_available and self.consecutive_failures < self.max_failures
    
    def get_health_score(self) -> float:
        """Calcula score de saúde da fonte (0-1)"""
        if not self.is_available:
            return 0.0
        
        # Score baseado em falhas recentes
        failure_penalty = self.consecutive_failures * 0.2
        base_score = 1.0 - failure_penalty
        
        # Bonus por sucesso recente
        if self.last_success:
            time_since_success = (datetime.now() - self.last_success).total_seconds()
            if time_since_success < 3600:  # 1 hora
                base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
