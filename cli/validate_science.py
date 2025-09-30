#!/usr/bin/env python3
"""
CLI para validação científica do modelo FED-Selic
"""

import argparse
import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.validation.scientific_validator import ScientificValidator
from src.validation.config import ValidationConfig
from src.validation.reporter import ValidationReporter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationCLI:
    """CLI para validação científica"""
    
    def __init__(self):
        self.config = ValidationConfig()
        self.validator = ScientificValidator()
        self.reporter = ValidationReporter()
        
        # Gerar seed global e hashes
        self.global_seed = self._generate_seed()
        self.data_hash = self._calculate_data_hash()
        self.code_hash = self._calculate_code_hash()
    
    def _generate_seed(self) -> int:
        """Gerar seed global para reprodutibilidade"""
        return int(datetime.now().timestamp() * 1000) % 2**32
    
    def _calculate_data_hash(self) -> str:
        """Calcular hash dos dados de treinamento"""
        try:
            data_path = self.config.data_path
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    content = f.read()
                return hashlib.sha256(content).hexdigest()
            return "no_data"
        except Exception as e:
            logger.warning(f"Erro ao calcular hash dos dados: {e}")
            return "error"
    
    def _calculate_code_hash(self) -> str:
        """Calcular hash do código (commit atual)"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=root_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "no_git"
        except Exception as e:
            logger.warning(f"Erro ao calcular hash do código: {e}")
            return "error"
    
    def run_validation(self, test_type: str, model_version: str = "latest") -> Dict[str, Any]:
        """Executar validação específica"""
        logger.info(f"🔬 Executando validação: {test_type}")
        logger.info(f"   Modelo: {model_version}")
        logger.info(f"   Seed: {self.global_seed}")
        logger.info(f"   Data hash: {self.data_hash[:8]}...")
        logger.info(f"   Code hash: {self.code_hash[:8]}...")
        
        # Executar teste específico
        if test_type == "size":
            results = self.validator.test_size_properties(seed=self.global_seed)
        elif test_type == "power":
            results = self.validator.test_power_properties(seed=self.global_seed)
        elif test_type == "hetero":
            results = self.validator.test_heteroskedasticity(seed=self.global_seed)
        elif test_type == "breaks":
            results = self.validator.test_structural_breaks(seed=self.global_seed)
        elif test_type == "small":
            results = self.validator.test_small_samples(seed=self.global_seed)
        elif test_type == "benchmarks":
            results = self.validator.test_nelson_plosser_benchmarks(seed=self.global_seed)
        elif test_type == "lags":
            results = self.validator.test_lag_selection(seed=self.global_seed)
        elif test_type == "all":
            results = self.validator.run_all_tests(seed=self.global_seed)
        else:
            raise ValueError(f"Tipo de teste inválido: {test_type}")
        
        # Adicionar metadados
        results["metadata"] = {
            "test_type": test_type,
            "model_version": model_version,
            "timestamp": datetime.utcnow().isoformat(),
            "global_seed": self.global_seed,
            "data_hash": self.data_hash,
            "code_hash": self.code_hash,
            "config": self.config.to_dict()
        }
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """Gerar relatório de validação"""
        if output_dir is None:
            output_dir = f"reports/validation/{datetime.now().strftime('%Y-%m-%d')}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Gerar relatório Markdown
        md_report = self.reporter.generate_markdown_report(results)
        md_path = os.path.join(output_dir, f"validation_{results['metadata']['test_type']}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        # Gerar relatório JSON
        json_path = os.path.join(output_dir, f"validation_{results['metadata']['test_type']}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Relatório gerado:")
        logger.info(f"   Markdown: {md_path}")
        logger.info(f"   JSON: {json_path}")
        
        return output_dir
    
    def check_promotion_gate(self, results: Dict[str, Any]) -> bool:
        """Verificar se modelo pode ser promovido"""
        logger.info("🚪 Verificando gate de promoção...")
        
        # Verificar critérios mínimos
        criteria = self.config.promotion_criteria
        
        # Cobertura 95% CI
        if "coverage_95" in results:
            coverage_95 = results["coverage_95"]
            if coverage_95 < criteria["min_coverage_95"]:
                logger.error(f"❌ Cobertura 95% insuficiente: {coverage_95:.3f} < {criteria['min_coverage_95']}")
                return False
        
        # Calibração (ECE)
        if "ece" in results:
            ece = results["ece"]
            if ece > criteria["max_ece"]:
                logger.error(f"❌ ECE muito alto: {ece:.3f} > {criteria['max_ece']}")
                return False
        
        # Brier Score
        if "brier_score" in results:
            brier = results["brier_score"]
            if brier > criteria["max_brier_score"]:
                logger.error(f"❌ Brier Score muito alto: {brier:.3f} > {criteria['max_brier_score']}")
                return False
        
        # CRPS
        if "crps" in results:
            crps = results["crps"]
            if crps > criteria["max_crps"]:
                logger.error(f"❌ CRPS muito alto: {crps:.3f} > {criteria['max_crps']}")
                return False
        
        logger.info("✅ Gate de promoção: APROVADO")
        return True

def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Validação científica do modelo FED-Selic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python cli/validate_science.py size --model-version v1.0.0
  python cli/validate_science.py all --output-dir reports/validation/2025-01-15
  python cli/validate_science.py benchmarks --check-gate
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["size", "power", "hetero", "breaks", "small", "benchmarks", "lags", "all"],
        help="Tipo de teste a executar"
    )
    
    parser.add_argument(
        "--model-version",
        default="latest",
        help="Versão do modelo a validar"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Diretório de saída dos relatórios"
    )
    
    parser.add_argument(
        "--check-gate",
        action="store_true",
        help="Verificar gate de promoção após validação"
    )
    
    parser.add_argument(
        "--config",
        help="Arquivo de configuração personalizado"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Logs detalhados"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Inicializar CLI
        cli = ValidationCLI()
        
        # Carregar configuração personalizada se fornecida
        if args.config:
            cli.config.load_from_file(args.config)
        
        # Executar validação
        results = cli.run_validation(args.test_type, args.model_version)
        
        # Gerar relatório
        output_dir = cli.generate_report(results, args.output_dir)
        
        # Verificar gate de promoção se solicitado
        if args.check_gate:
            approved = cli.check_promotion_gate(results)
            if not approved:
                sys.exit(1)
        
        logger.info("✅ Validação científica concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
