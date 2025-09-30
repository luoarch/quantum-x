"""
Logging Service - Single Responsibility Principle
Serviço responsável por logging estruturado
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from src.core.interfaces import ILoggingService

class LoggingService(ILoggingService):
    """
    Serviço de logging estruturado
    
    Responsabilidades:
    - Log de requests de previsão
    - Log de responses de previsão
    - Log de erros
    - Logging estruturado para auditoria
    """
    
    def __init__(self, 
                 log_level: str = "INFO",
                 log_format: str = "json",
                 log_file: Optional[str] = None):
        self.log_level = log_level
        self.log_format = log_format
        self.log_file = log_file
        
        # Configurar logger
        self.logger = logging.getLogger("quantum_x")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Configurar handler
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        
        # Configurar formato
        if log_format == "json":
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    async def log_prediction_request(self, request_id: str, request: Dict[str, Any]) -> None:
        """Log de request de previsão"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "prediction_request",
            "request_id": request_id,
            "level": "INFO",
            "data": {
                "fed_decision_date": request.get("fed_decision_date"),
                "fed_move_bps": request.get("fed_move_bps"),
                "fed_move_dir": request.get("fed_move_dir"),
                "horizons_months": request.get("horizons_months"),
                "model_version": request.get("model_version"),
                "regime_hint": request.get("regime_hint")
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_prediction_response(self, request_id: str, response: Dict[str, Any]) -> None:
        """Log de response de previsão"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "prediction_response",
            "request_id": request_id,
            "level": "INFO",
            "data": {
                "expected_move_bps": response.get("expected_move_bps"),
                "horizon_months": response.get("horizon_months"),
                "prob_move_within_next_copom": response.get("prob_move_within_next_copom"),
                "model_version": response.get("model_metadata", {}).get("version"),
                "processing_time_ms": response.get("processing_time_ms"),
                "cache_hit": response.get("cache_hit", False)
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_error(self, request_id: str, error: Exception) -> None:
        """Log de erro"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "request_id": request_id,
            "level": "ERROR",
            "data": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_code": getattr(error, 'error_code', 'UNKNOWN_ERROR'),
                "error_details": getattr(error, 'details', {})
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_model_training(self, model_version: str, training_data: Dict[str, Any]) -> None:
        """Log de treinamento de modelo"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "model_training",
            "model_version": model_version,
            "level": "INFO",
            "data": {
                "n_observations": training_data.get("n_observations"),
                "data_hash": training_data.get("data_hash"),
                "methodology": training_data.get("methodology"),
                "r_squared": training_data.get("r_squared"),
                "training_time_seconds": training_data.get("training_time_seconds")
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_model_evaluation(self, model_version: str, evaluation_metrics: Dict[str, Any]) -> None:
        """Log de avaliação de modelo"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "model_evaluation",
            "model_version": model_version,
            "level": "INFO",
            "data": {
                "r_squared": evaluation_metrics.get("r_squared"),
                "mae": evaluation_metrics.get("mae"),
                "rmse": evaluation_metrics.get("rmse"),
                "coverage_80": evaluation_metrics.get("coverage_80"),
                "coverage_95": evaluation_metrics.get("coverage_95"),
                "brier_score": evaluation_metrics.get("brier_score")
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_data_quality(self, source: str, quality_metrics: Dict[str, Any]) -> None:
        """Log de qualidade de dados"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_quality",
            "source": source,
            "level": "INFO",
            "data": {
                "completeness": quality_metrics.get("completeness"),
                "consistency": quality_metrics.get("consistency"),
                "timeliness": quality_metrics.get("timeliness"),
                "accuracy": quality_metrics.get("accuracy"),
                "overall_score": quality_metrics.get("overall_score"),
                "issues": quality_metrics.get("issues", [])
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_api_access(self, endpoint: str, method: str, status_code: int, 
                           processing_time_ms: float, user_id: Optional[str] = None) -> None:
        """Log de acesso à API"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "api_access",
            "level": "INFO",
            "data": {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "processing_time_ms": processing_time_ms,
                "user_id": user_id
            }
        }
        
        self._log_structured(log_entry)
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log de evento de segurança"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "security_event",
            "security_event_type": event_type,
            "level": "WARNING",
            "data": details
        }
        
        self._log_structured(log_entry)
    
    def _log_structured(self, log_entry: Dict[str, Any]) -> None:
        """Log estruturado"""
        if self.log_format == "json":
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        else:
            # Formato legível para desenvolvimento
            message = f"{log_entry['event_type']} - {log_entry.get('request_id', 'N/A')}"
            if 'data' in log_entry:
                message += f" - {json.dumps(log_entry['data'], ensure_ascii=False)}"
            self.logger.info(message)
    
    async def cleanup(self):
        """Cleanup do serviço"""
        # Fechar handlers de arquivo se necessário
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
