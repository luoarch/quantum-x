"""
Validation Service - Single Responsibility Principle
Serviço responsável por validação de dados e requests
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import re

from src.core.interfaces import IValidationService
from src.core.exceptions import ValidationError
from src.core.models import FedDecision, PredictionRequest

class ValidationService(IValidationService):
    """
    Serviço de validação de dados
    
    Responsabilidades:
    - Validar dados do Fed
    - Validar dados da Selic
    - Validar requests de previsão
    - Aplicar regras de negócio
    """
    
    def __init__(self, validation_rules: Dict[str, Any] = None):
        self.validation_rules = validation_rules or {}
        
        # Regras padrão conforme requisitos
        self.fed_move_bps_range = self.validation_rules.get('fed_move_bps_range', (-200, 200))
        self.horizons_months_range = self.validation_rules.get('horizons_months_range', (1, 24))
        self.max_batch_size = self.validation_rules.get('max_batch_size', 10)
        self.fed_move_step = 25  # Múltiplos de 25 bps conforme requisitos
    
    async def validate_fed_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar dados do Fed"""
        errors = []
        
        try:
            # Verificar campos obrigatórios
            required_fields = ['date', 'fed_funds_rate', 'fed_move_bps']
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            if errors:
                return False, errors
            
            # Validar data
            if isinstance(data['date'], str):
                try:
                    data['date'] = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                except ValueError:
                    errors.append("Formato de data inválido")
            
            # Validar taxa de juros
            if not isinstance(data['fed_funds_rate'], (int, float)):
                errors.append("fed_funds_rate deve ser numérico")
            elif not (0 <= data['fed_funds_rate'] <= 20):
                errors.append("fed_funds_rate deve estar entre 0% e 20%")
            
            # Validar movimento em bps
            if not isinstance(data['fed_move_bps'], (int, float)):
                errors.append("fed_move_bps deve ser numérico")
            elif data['fed_move_bps'] % self.fed_move_step != 0:
                errors.append(f"fed_move_bps deve ser múltiplo de {self.fed_move_step}")
            elif not (self.fed_move_bps_range[0] <= data['fed_move_bps'] <= self.fed_move_bps_range[1]):
                errors.append(f"fed_move_bps deve estar entre {self.fed_move_bps_range[0]} e {self.fed_move_bps_range[1]}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Erro na validação: {str(e)}"]
    
    async def validate_selic_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar dados da Selic"""
        errors = []
        
        try:
            # Verificar campos obrigatórios
            required_fields = ['date', 'selic_rate', 'selic_move_bps']
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            if errors:
                return False, errors
            
            # Validar data
            if isinstance(data['date'], str):
                try:
                    data['date'] = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                except ValueError:
                    errors.append("Formato de data inválido")
            
            # Validar taxa Selic
            if not isinstance(data['selic_rate'], (int, float)):
                errors.append("selic_rate deve ser numérico")
            elif not (0 <= data['selic_rate'] <= 50):
                errors.append("selic_rate deve estar entre 0% e 50%")
            
            # Validar movimento em bps
            if not isinstance(data['selic_move_bps'], (int, float)):
                errors.append("selic_move_bps deve ser numérico")
            elif data['selic_move_bps'] % self.fed_move_step != 0:
                errors.append(f"selic_move_bps deve ser múltiplo de {self.fed_move_step}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Erro na validação: {str(e)}"]
    
    async def validate_prediction_request(self, request: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar request de previsão conforme requisitos"""
        errors = []
        
        try:
            # Validar campos obrigatórios
            required_fields = ['fed_decision_date', 'fed_move_bps']
            for field in required_fields:
                if field not in request or request[field] is None:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            if errors:
                return False, errors
            
            # Validar fed_decision_date
            if not isinstance(request['fed_decision_date'], str):
                errors.append("fed_decision_date deve ser string")
            else:
                try:
                    decision_date = datetime.fromisoformat(request['fed_decision_date'].replace('Z', '+00:00'))
                    
                    # Não pode ser futuro além de um limite (conforme requisitos)
                    max_future_days = 30
                    if decision_date > datetime.now() + timedelta(days=max_future_days):
                        errors.append(f"fed_decision_date não pode ser mais de {max_future_days} dias no futuro")
                    
                except ValueError:
                    errors.append("fed_decision_date deve estar no formato ISO-8601")
            
            # Validar fed_move_bps
            if not isinstance(request['fed_move_bps'], int):
                errors.append("fed_move_bps deve ser inteiro")
            elif request['fed_move_bps'] % self.fed_move_step != 0:
                errors.append(f"fed_move_bps deve ser múltiplo de {self.fed_move_step}")
            elif not (self.fed_move_bps_range[0] <= request['fed_move_bps'] <= self.fed_move_bps_range[1]):
                errors.append(f"fed_move_bps deve estar entre {self.fed_move_bps_range[0]} e {self.fed_move_bps_range[1]}")
            
            # Validar fed_move_dir (opcional)
            if 'fed_move_dir' in request and request['fed_move_dir'] is not None:
                if request['fed_move_dir'] not in [-1, 0, 1]:
                    errors.append("fed_move_dir deve ser -1, 0 ou 1")
            
            # Validar fed_surprise_bps (opcional)
            if 'fed_surprise_bps' in request and request['fed_surprise_bps'] is not None:
                if not isinstance(request['fed_surprise_bps'], int):
                    errors.append("fed_surprise_bps deve ser inteiro")
                elif not (-100 <= request['fed_surprise_bps'] <= 100):
                    errors.append("fed_surprise_bps deve estar entre -100 e 100")
            
            # Validar horizons_months
            if 'horizons_months' in request and request['horizons_months'] is not None:
                if not isinstance(request['horizons_months'], list):
                    errors.append("horizons_months deve ser array")
                elif not request['horizons_months']:
                    errors.append("horizons_months não pode estar vazio")
                else:
                    for h in request['horizons_months']:
                        if not isinstance(h, int):
                            errors.append("Elementos de horizons_months devem ser inteiros")
                        elif not (self.horizons_months_range[0] <= h <= self.horizons_months_range[1]):
                            errors.append(f"Elementos de horizons_months devem estar entre {self.horizons_months_range[0]} e {self.horizons_months_range[1]}")
            
            # Validar model_version (opcional)
            if 'model_version' in request and request['model_version'] is not None:
                if not isinstance(request['model_version'], str):
                    errors.append("model_version deve ser string")
                elif not re.match(r'^v\d+\.\d+\.\d+$', request['model_version']):
                    errors.append("model_version deve seguir formato vX.Y.Z")
            
            # Validar regime_hint (opcional)
            if 'regime_hint' in request and request['regime_hint'] is not None:
                valid_regimes = ['normal', 'stress', 'crisis', 'recovery']
                if request['regime_hint'] not in valid_regimes:
                    errors.append(f"regime_hint deve ser um dos: {', '.join(valid_regimes)}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Erro na validação: {str(e)}"]
    
    async def validate_batch_request(self, requests: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validar request em lote"""
        errors = []
        
        # Validar tamanho do lote
        if len(requests) > self.max_batch_size:
            errors.append(f"Máximo de {self.max_batch_size} cenários por lote")
        
        if not requests:
            errors.append("Lista de cenários não pode estar vazia")
        
        # Validar cada request individualmente
        for i, request in enumerate(requests):
            is_valid, request_errors = await self.validate_prediction_request(request)
            if not is_valid:
                errors.extend([f"Cenário {i+1}: {error}" for error in request_errors])
        
        return len(errors) == 0, errors
    
    def validate_fed_decision(self, fed_decision: FedDecision) -> Tuple[bool, List[str]]:
        """Validar objeto FedDecision"""
        errors = []
        
        # Validar data
        if fed_decision.date > datetime.now() + timedelta(days=30):
            errors.append("Data da decisão não pode ser mais de 30 dias no futuro")
        
        # Validar movimento
        if fed_decision.move_bps % self.fed_move_step != 0:
            errors.append(f"move_bps deve ser múltiplo de {self.fed_move_step}")
        
        if not (self.fed_move_bps_range[0] <= fed_decision.move_bps <= self.fed_move_bps_range[1]):
            errors.append(f"move_bps deve estar entre {self.fed_move_bps_range[0]} e {self.fed_move_bps_range[1]}")
        
        # Validar direção
        if fed_decision.direction not in [-1, 0, 1]:
            errors.append("direction deve ser -1, 0 ou 1")
        
        # Validar surpresa
        if fed_decision.surprise_bps is not None:
            if not (-100 <= fed_decision.surprise_bps <= 100):
                errors.append("surprise_bps deve estar entre -100 e 100")
        
        return len(errors) == 0, errors
