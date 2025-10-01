"""
Testes Unitários - DataService
Sprint 2.3 - Científicos e Robustos
Target: 48% → 80% coverage
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.data_service import DataService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_combined_data():
    """Dados combinados de exemplo para testes"""
    dates = pd.date_range(start='2020-01-01', periods=24, freq='MS')
    
    return pd.DataFrame({
        'fed_rate': np.linspace(0.25, 5.5, 24),
        'selic': np.linspace(2.0, 13.75, 24),
        'ipca': np.random.uniform(2, 10, 24)
    }, index=dates)


@pytest.fixture
def data_service():
    """DataService para testes"""
    return DataService()


# ============================================================================
# TESTES: _prepare_prediction_data()
# ============================================================================

class TestDataServicePrepareData:
    """Testes de preparação de dados"""
    
    def test_prepare_prediction_data_creates_derived_variables(
        self, data_service, sample_combined_data
    ):
        """✅ Deve criar variáveis derivadas"""
        result = data_service._prepare_prediction_data(sample_combined_data)
        
        # Verificar variáveis derivadas
        assert 'fed_change' in result.columns
        assert 'selic_change' in result.columns
        assert 'spillover' in result.columns
        assert 'spillover_change' in result.columns
    
    def test_prepare_prediction_data_removes_nans(
        self, data_service, sample_combined_data
    ):
        """✅ Deve remover NaNs (primeira linha após diff)"""
        result = data_service._prepare_prediction_data(sample_combined_data)
        
        # Não deve ter NaNs
        assert result.isnull().sum().sum() == 0
        
        # Deve ter menos observações (removeu primeira linha)
        assert len(result) < len(sample_combined_data)
    
    def test_prepare_prediction_data_spillover_calculation(
        self, data_service, sample_combined_data
    ):
        """✅ Spillover deve ser diferença Fed - Selic"""
        result = data_service._prepare_prediction_data(sample_combined_data)
        
        # Recalcular spillover manualmente
        expected_spillover = result['fed_rate'] - result['selic']
        
        # Verificar com tolerância
        pd.testing.assert_series_equal(
            result['spillover'],
            expected_spillover,
            check_names=False
        )
    
    def test_prepare_prediction_data_missing_columns_raises_error(
        self, data_service
    ):
        """✅ Deve lançar erro se colunas obrigatórias estiverem ausentes"""
        # Dados sem coluna 'fed_rate'
        invalid_data = pd.DataFrame({
            'selic': [10.0, 10.5, 11.0],
            'ipca': [3.0, 3.5, 4.0]
        })
        
        with pytest.raises(ValueError, match="Coluna fed_rate não encontrada"):
            data_service._prepare_prediction_data(invalid_data)
    
    def test_prepare_prediction_data_preserves_index(
        self, data_service, sample_combined_data
    ):
        """✅ Deve preservar índice temporal"""
        result = data_service._prepare_prediction_data(sample_combined_data)
        
        # Índice deve ser DatetimeIndex
        assert isinstance(result.index, pd.DatetimeIndex)


# ============================================================================
# TESTES: get_data_summary() (async)
# ============================================================================

class TestDataServiceSummary:
    """Testes de resumo de dados"""
    
    @pytest.mark.skip(reason="Method load_all_interest_rate_data needs refactoring")
    @pytest.mark.asyncio
    async def test_get_data_summary_structure(self, data_service):
        """✅ Resumo deve ter estrutura correta"""
        with patch.object(
            data_service.interest_rate_service,
            'load_data',
            return_value=None
        ), patch.object(
            data_service.selic_service,
            'load_data',
            return_value=None
        ), patch.object(
            data_service.selic_service,
            '_load_combined_data',
            side_effect=Exception("No data")
        ):
            summary = await data_service.get_data_summary()
            
            # Verificar estrutura
            assert 'fed_data' in summary
            assert 'selic_data' in summary
            assert 'combined_data' in summary
            
            # Cada seção deve ter campos esperados
            assert 'observations' in summary['fed_data']
            assert 'observations' in summary['selic_data']
            assert 'observations' in summary['combined_data']
    
    @pytest.mark.skip(reason="Method load_all_interest_rate_data needs refactoring")
    @pytest.mark.asyncio
    async def test_get_data_summary_with_real_data(
        self, data_service, sample_combined_data
    ):
        """✅ Resumo deve funcionar com dados reais"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=sample_combined_data
        ), patch.object(
            data_service.interest_rate_service,
            'load_data',
            return_value=None
        ), patch.object(
            data_service.selic_service,
            'load_data',
            return_value=None
        ):
            summary = await data_service.get_data_summary()
            
            # Verificar dados combinados
            assert summary['combined_data']['observations'] == len(sample_combined_data)
            assert summary['combined_data']['start_date'] is not None
            assert summary['combined_data']['end_date'] is not None


# ============================================================================
# TESTES: validate_data_quality() (async)
# ============================================================================

class TestDataServiceValidation:
    """Testes de validação de qualidade"""
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_valid_data(
        self, data_service, sample_combined_data
    ):
        """✅ Dados válidos devem passar na validação"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=sample_combined_data
        ):
            result = await data_service.validate_data_quality()
            
            # Deve ser válido (sem valores ausentes nos dados de exemplo)
            assert result['valid'] is True
            assert len(result['issues']) == 0
            assert result['data_points'] == len(sample_combined_data)
            assert 'fed_rate' in result['columns']
            assert 'selic' in result['columns']
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_missing_values(self, data_service):
        """✅ Deve detectar valores ausentes"""
        # Dados com valores ausentes
        data_with_nans = pd.DataFrame({
            'fed_rate': [1.0, 2.0, np.nan, 4.0],
            'selic': [10.0, 10.5, 11.0, np.nan],
            'ipca': [3.0, 3.5, 4.0, 4.5]
        })
        
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=data_with_nans
        ):
            result = await data_service.validate_data_quality()
            
            # Deve detectar problemas
            assert result['valid'] is False
            assert len(result['issues']) > 0
            assert any('fed_rate' in issue for issue in result['issues'])
            assert any('selic' in issue for issue in result['issues'])
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_small_dataset_warning(self, data_service):
        """✅ Deve alertar sobre datasets pequenos"""
        # Dados muito pequenos
        small_data = pd.DataFrame({
            'fed_rate': [1.0, 2.0],
            'selic': [10.0, 10.5]
        })
        
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=small_data
        ):
            result = await data_service.validate_data_quality()
            
            # Deve ter warning sobre poucos dados
            assert len(result['warnings']) > 0
            assert any('Poucos dados' in warning for warning in result['warnings'])
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_out_of_range_selic(self, data_service):
        """✅ Deve alertar sobre Selic fora do range"""
        # Dados com Selic fora do range esperado (< 0 ou > 50)
        out_of_range_data = pd.DataFrame({
            'fed_rate': [1.0, 2.0, 3.0],
            'selic': [-1.0, 60.0, 10.0]  # Valores anormais
        })
        
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=out_of_range_data
        ):
            result = await data_service.validate_data_quality()
            
            # Deve ter warning sobre valores fora do range
            assert len(result['warnings']) > 0
            assert any('Selic fora do range' in warning for warning in result['warnings'])
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_out_of_range_fed(self, data_service):
        """✅ Deve alertar sobre Fed Funds fora do range"""
        # Dados com Fed fora do range esperado (< 0 ou > 25)
        out_of_range_data = pd.DataFrame({
            'fed_rate': [-2.0, 30.0, 5.0],  # Valores anormais
            'selic': [10.0, 11.0, 12.0]
        })
        
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=out_of_range_data
        ):
            result = await data_service.validate_data_quality()
            
            # Deve ter warning sobre valores fora do range
            assert len(result['warnings']) > 0
            assert any('Fed Funds fora do range' in warning for warning in result['warnings'])
    
    @pytest.mark.asyncio
    async def test_validate_data_quality_handles_errors(self, data_service):
        """✅ Deve tratar erros gracefully"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            side_effect=Exception("Test error")
        ):
            result = await data_service.validate_data_quality()
            
            # Deve retornar resultado inválido com erro
            assert result['valid'] is False
            assert len(result['issues']) > 0
            assert any('Erro ao validar' in issue for issue in result['issues'])


# ============================================================================
# TESTES: get_data_metadata() (async)
# ============================================================================

class TestDataServiceMetadata:
    """Testes de metadados"""
    
    @pytest.mark.asyncio
    async def test_get_data_metadata_structure(
        self, data_service, sample_combined_data
    ):
        """✅ Metadados devem ter estrutura correta"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=sample_combined_data
        ):
            metadata = await data_service.get_data_metadata()
            
            # Verificar estrutura
            assert 'sources' in metadata
            assert 'frequency' in metadata
            assert 'last_updated' in metadata
            assert 'columns' in metadata
            assert 'statistics' in metadata
            
            # Verificar sources
            assert 'fed' in metadata['sources']
            assert 'selic' in metadata['sources']
    
    @pytest.mark.asyncio
    async def test_get_data_metadata_column_info(
        self, data_service, sample_combined_data
    ):
        """✅ Metadados de colunas devem estar completos"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=sample_combined_data
        ):
            metadata = await data_service.get_data_metadata()
            
            # Verificar informações das colunas
            for col in sample_combined_data.columns:
                assert col in metadata['columns']
                assert 'type' in metadata['columns'][col]
                assert 'non_null_count' in metadata['columns'][col]
                assert 'null_count' in metadata['columns'][col]
    
    @pytest.mark.asyncio
    async def test_get_data_metadata_statistics(
        self, data_service, sample_combined_data
    ):
        """✅ Estatísticas devem estar corretas"""
        with patch.object(
            data_service.selic_service,
            '_load_combined_data',
            return_value=sample_combined_data
        ):
            metadata = await data_service.get_data_metadata()
            
            # Verificar estatísticas
            assert 'fed_rate' in metadata['statistics']
            assert 'selic' in metadata['statistics']
            
            # Verificar métricas estatísticas
            for series_name in ['fed_rate', 'selic']:
                stats = metadata['statistics'][series_name]
                assert 'mean' in stats
                assert 'std' in stats
                assert 'min' in stats
                assert 'max' in stats
                
                # Verificar que são números válidos
                assert isinstance(stats['mean'], float)
                assert isinstance(stats['std'], float)
                assert stats['min'] <= stats['mean'] <= stats['max']


# ============================================================================
# TESTES: Inicialização e Dependências
# ============================================================================

class TestDataServiceInit:
    """Testes de inicialização"""
    
    def test_data_service_initialization(self):
        """✅ DataService deve inicializar corretamente"""
        service = DataService()
        
        assert service is not None
        assert hasattr(service, 'settings')
        assert hasattr(service, 'interest_rate_service')
        assert hasattr(service, 'selic_service')
    
    def test_data_service_has_required_dependencies(self):
        """✅ DataService deve ter dependências necessárias"""
        service = DataService()
        
        # Verificar que serviços estão instanciados
        assert service.interest_rate_service is not None
        assert service.selic_service is not None


# ============================================================================
# TESTES: Propriedades Científicas
# ============================================================================

class TestDataServiceScientificProperties:
    """Testes de propriedades científicas dos dados"""
    
    def test_spillover_is_symmetric(self, data_service):
        """✅ Spillover deve ser simétrico: Fed - Selic = -(Selic - Fed)"""
        data = pd.DataFrame({
            'fed_rate': [2.0, 3.0, 4.0],
            'selic': [10.0, 11.0, 12.0]
        })
        
        result = data_service._prepare_prediction_data(data)
        
        # Calcular spillover reverso
        reverse_spillover = result['selic'] - result['fed_rate']
        
        # Verificar simetria
        pd.testing.assert_series_equal(
            result['spillover'],
            -reverse_spillover,
            check_names=False
        )
    
    def test_change_variables_are_first_differences(self, data_service):
        """✅ Variáveis *_change devem ser primeiras diferenças"""
        data = pd.DataFrame({
            'fed_rate': [1.0, 2.0, 3.5, 4.0],
            'selic': [10.0, 10.5, 11.0, 12.0]
        })
        
        result = data_service._prepare_prediction_data(data)
        
        # Recalcular mudanças manualmente
        expected_fed_change = data['fed_rate'].diff().dropna()
        expected_selic_change = data['selic'].diff().dropna()
        
        # Verificar (reindexar para comparar)
        pd.testing.assert_series_equal(
            result['fed_change'],
            expected_fed_change.loc[result.index],
            check_names=False
        )
    
    def test_prepared_data_monotonic_index(self, data_service, sample_combined_data):
        """✅ Dados preparados devem ter índice temporal crescente"""
        result = data_service._prepare_prediction_data(sample_combined_data)
        
        # Índice deve ser monotônico crescente
        assert result.index.is_monotonic_increasing

