"""
Sistema de relatórios para validação científica
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ValidationReporter:
    """Gerador de relatórios de validação científica"""
    
    def __init__(self):
        self.template_dir = "templates/validation"
        self.figures_dir = "figures"
    
    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório em Markdown"""
        metadata = results.get("metadata", {})
        test_type = metadata.get("test_type", "unknown")
        timestamp = metadata.get("timestamp", datetime.utcnow().isoformat())
        
        report = f"""# Relatório de Validação Científica

## Informações Gerais

- **Tipo de Teste**: {test_type.upper()}
- **Data/Hora**: {timestamp}
- **Modelo**: {metadata.get('model_version', 'N/A')}
- **Seed Global**: {metadata.get('global_seed', 'N/A')}
- **Hash dos Dados**: `{metadata.get('data_hash', 'N/A')[:8]}...`
- **Hash do Código**: `{metadata.get('code_hash', 'N/A')[:8]}...`

## Resultados

"""
        
        # Adicionar seções específicas baseadas no tipo de teste
        if test_type == "size":
            report += self._generate_size_report(results)
        elif test_type == "power":
            report += self._generate_power_report(results)
        elif test_type == "hetero":
            report += self._generate_hetero_report(results)
        elif test_type == "breaks":
            report += self._generate_breaks_report(results)
        elif test_type == "small":
            report += self._generate_small_samples_report(results)
        elif test_type == "benchmarks":
            report += self._generate_benchmarks_report(results)
        elif test_type == "lags":
            report += self._generate_lag_selection_report(results)
        elif test_type == "all":
            report += self._generate_all_tests_report(results)
        else:
            report += self._generate_generic_report(results)
        
        # Adicionar seção de conclusões
        report += self._generate_conclusions(results)
        
        # Adicionar rodapé
        report += f"""
---

*Relatório gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Sistema de Validação Científica FED-Selic*
"""
        
        return report
    
    def _generate_size_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de propriedades de size"""
        report = "### Propriedades de Size\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Tabela de resultados por tamanho de amostra
        if "size_results" in results:
            report += "#### Resultados por Tamanho de Amostra\n\n"
            report += "| T | ADF | KPSS | DF-GLS | Status |\n"
            report += "|---|-----|------|--------|--------|\n"
            
            for size_result in results["size_results"]:
                T = size_result.get("T", "N/A")
                adf = size_result.get("adf_size", "N/A")
                kpss = size_result.get("kpss_size", "N/A")
                dfgls = size_result.get("dfgls_size", "N/A")
                status = "✅" if size_result.get("passed", False) else "❌"
                
                report += f"| {T} | {adf:.3f} | {kpss:.3f} | {dfgls:.3f} | {status} |\n"
        
        # Resumo estatístico
        if "summary" in results:
            summary = results["summary"]
            report += f"\n#### Resumo Estatístico\n\n"
            report += f"- **Testes Aprovados**: {summary.get('passed', 0)}/{summary.get('total', 0)}\n"
            report += f"- **Taxa de Sucesso**: {summary.get('success_rate', 0):.1%}\n"
            report += f"- **Status Geral**: {summary.get('overall_status', 'N/A')}\n"
        
        return report
    
    def _generate_power_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de propriedades de poder"""
        report = "### Propriedades de Poder\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Tabela de poder por alternativa
        if "power_results" in results:
            report += "#### Poder por Alternativa\n\n"
            report += "| Alternativa | ADF | KPSS | DF-GLS | Melhor |\n"
            report += "|-------------|-----|------|--------|--------|\n"
            
            for power_result in results["power_results"]:
                alt = power_result.get("alternative", "N/A")
                adf = power_result.get("adf_power", "N/A")
                kpss = power_result.get("kpss_power", "N/A")
                dfgls = power_result.get("dfgls_power", "N/A")
                best = power_result.get("best_test", "N/A")
                
                report += f"| {alt} | {adf:.3f} | {kpss:.3f} | {dfgls:.3f} | {best} |\n"
        
        return report
    
    def _generate_hetero_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de heterocedasticidade"""
        report = "### Robustez à Heterocedasticidade\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Resultados por configuração de heterocedasticidade
        if "hetero_results" in results:
            report += "#### Resultados por Configuração\n\n"
            report += "| Configuração | ADF | KPSS | DF-GLS | Status |\n"
            report += "|--------------|-----|------|--------|--------|\n"
            
            for hetero_result in results["hetero_results"]:
                config = hetero_result.get("config", "N/A")
                adf = hetero_result.get("adf_rejection", "N/A")
                kpss = hetero_result.get("kpss_rejection", "N/A")
                dfgls = hetero_result.get("dfgls_rejection", "N/A")
                status = "✅" if hetero_result.get("passed", False) else "❌"
                
                report += f"| {config} | {adf:.3f} | {kpss:.3f} | {dfgls:.3f} | {status} |\n"
        
        return report
    
    def _generate_breaks_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de quebras estruturais"""
        report = "### Detecção de Quebras Estruturais\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Resultados por configuração de quebra
        if "break_results" in results:
            report += "#### Resultados por Configuração de Quebra\n\n"
            report += "| Configuração | Detecção | Taxa | Status |\n"
            report += "|--------------|----------|------|--------|\n"
            
            for break_result in results["break_results"]:
                config = break_result.get("config", "N/A")
                detection = break_result.get("detection_rate", "N/A")
                rate = break_result.get("detection_rate", "N/A")
                status = "✅" if break_result.get("passed", False) else "❌"
                
                report += f"| {config} | {detection:.3f} | {rate:.1%} | {status} |\n"
        
        return report
    
    def _generate_small_samples_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de amostras pequenas"""
        report = "### Propriedades com Amostras Pequenas\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Resultados por tamanho de amostra pequena
        if "small_sample_results" in results:
            report += "#### Resultados por Tamanho de Amostra\n\n"
            report += "| T | ADF | KPSS | DF-GLS | Status |\n"
            report += "|---|-----|------|--------|--------|\n"
            
            for small_result in results["small_sample_results"]:
                T = small_result.get("T", "N/A")
                adf = small_result.get("adf_size", "N/A")
                kpss = small_result.get("kpss_size", "N/A")
                dfgls = small_result.get("dfgls_size", "N/A")
                status = "✅" if small_result.get("passed", False) else "❌"
                
                report += f"| {T} | {adf:.3f} | {kpss:.3f} | {dfgls:.3f} | {status} |\n"
        
        return report
    
    def _generate_benchmarks_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de benchmarks Nelson-Plosser"""
        report = "### Benchmarks Nelson-Plosser\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Resultados por série
        if "benchmark_results" in results:
            report += "#### Resultados por Série\n\n"
            report += "| Série | ADF | KPSS | DF-GLS | Esperado | Status |\n"
            report += "|-------|-----|------|--------|----------|--------|\n"
            
            for benchmark_result in results["benchmark_results"]:
                series = benchmark_result.get("series", "N/A")
                adf = benchmark_result.get("adf_result", "N/A")
                kpss = benchmark_result.get("kpss_result", "N/A")
                dfgls = benchmark_result.get("dfgls_result", "N/A")
                expected = benchmark_result.get("expected_order", "N/A")
                status = "✅" if benchmark_result.get("passed", False) else "❌"
                
                report += f"| {series} | {adf} | {kpss} | {dfgls} | I({expected}) | {status} |\n"
        
        return report
    
    def _generate_lag_selection_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de seleção de lags"""
        report = "### Seleção de Lags\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
            return report
        
        # Resultados por critério
        if "lag_results" in results:
            report += "#### Resultados por Critério\n\n"
            report += "| Critério | Lags Selecionados | Valor | Status |\n"
            report += "|----------|-------------------|-------|--------|\n"
            
            for lag_result in results["lag_results"]:
                criterion = lag_result.get("criterion", "N/A")
                lags = lag_result.get("selected_lags", "N/A")
                value = lag_result.get("criterion_value", "N/A")
                status = "✅" if lag_result.get("passed", False) else "❌"
                
                report += f"| {criterion} | {lags} | {value:.3f} | {status} |\n"
        
        return report
    
    def _generate_all_tests_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório de todos os testes"""
        report = "### Resumo de Todos os Testes\n\n"
        
        if "summary" in results:
            summary = results["summary"]
            report += f"- **Total de Testes**: {summary.get('total_tests', 0)}\n"
            report += f"- **Testes Aprovados**: {summary.get('passed_tests', 0)}\n"
            report += f"- **Testes Falharam**: {summary.get('failed_tests', 0)}\n"
            report += f"- **Testes Ignorados**: {summary.get('skipped_tests', 0)}\n"
            report += f"- **Status Geral**: {summary.get('overall_status', 'N/A')}\n\n"
        
        # Detalhes por teste
        if "tests" in results:
            report += "#### Detalhes por Teste\n\n"
            
            for test_name, test_result in results["tests"].items():
                status = "✅" if "error" not in test_result else "❌"
                report += f"- **{test_name.replace('_', ' ').title()}**: {status}\n"
                
                if "error" in test_result:
                    report += f"  - Erro: {test_result['error']}\n"
        
        return report
    
    def _generate_generic_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório genérico"""
        report = "### Resultados\n\n"
        
        if "error" in results:
            report += f"❌ **Erro**: {results['error']}\n\n"
        else:
            report += "✅ **Teste concluído com sucesso**\n\n"
            
            # Adicionar métricas principais se disponíveis
            if "coverage_95" in results:
                report += f"- **Cobertura 95%**: {results['coverage_95']:.3f}\n"
            if "ece" in results:
                report += f"- **ECE**: {results['ece']:.3f}\n"
            if "brier_score" in results:
                report += f"- **Brier Score**: {results['brier_score']:.3f}\n"
            if "crps" in results:
                report += f"- **CRPS**: {results['crps']:.3f}\n"
        
        return report
    
    def _generate_conclusions(self, results: Dict[str, Any]) -> str:
        """Gerar seção de conclusões"""
        report = "## Conclusões\n\n"
        
        # Determinar status geral
        if "error" in results:
            report += "❌ **O teste falhou devido a erros técnicos.**\n\n"
            report += "### Recomendações\n\n"
            report += "1. Verificar logs de erro para detalhes\n"
            report += "2. Verificar dependências e configurações\n"
            report += "3. Executar teste novamente\n"
        else:
            # Verificar critérios de qualidade
            passed_criteria = []
            failed_criteria = []
            
            if "coverage_95" in results:
                if results["coverage_95"] >= 0.85:
                    passed_criteria.append("Cobertura 95% adequada")
                else:
                    failed_criteria.append("Cobertura 95% insuficiente")
            
            if "ece" in results:
                if results["ece"] <= 0.10:
                    passed_criteria.append("Calibração adequada")
                else:
                    failed_criteria.append("Calibração inadequada")
            
            if passed_criteria:
                report += "✅ **Critérios Aprovados:**\n"
                for criterion in passed_criteria:
                    report += f"- {criterion}\n"
                report += "\n"
            
            if failed_criteria:
                report += "❌ **Critérios Falharam:**\n"
                for criterion in failed_criteria:
                    report += f"- {criterion}\n"
                report += "\n"
            
            if not passed_criteria and not failed_criteria:
                report += "ℹ️ **Teste concluído - verificar métricas específicas acima.**\n\n"
        
        return report
    
    def generate_json_report(self, results: Dict[str, Any]) -> str:
        """Gerar relatório em JSON"""
        return json.dumps(results, indent=2, ensure_ascii=False, default=str)
    
    def save_report(self, results: Dict[str, Any], output_dir: str, test_type: str) -> Dict[str, str]:
        """Salvar relatório em arquivos"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Gerar e salvar Markdown
        md_content = self.generate_markdown_report(results)
        md_path = os.path.join(output_dir, f"validation_{test_type}_{timestamp}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Gerar e salvar JSON
        json_content = self.generate_json_report(results)
        json_path = os.path.join(output_dir, f"validation_{test_type}_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        return {
            "markdown": md_path,
            "json": json_path
        }
