# 🥈 ROADMAP PRATA DETALHADO - QUANTUM-X

**Versão:** 2.0  
**Data:** 2025-10-01  
**Base:** Bronze 100% Certificado ✅  
**Prazo:** 30-60 dias (15 semanas)  

---

## 📋 RESUMO EXECUTIVO

### OBJETIVO PRATA

Evoluir de **Bronze** (modelo bivariado) para **Prata** (small VAR com 4 variáveis) mantendo rigor científico, auditabilidade e performance, com expansão de capacidades analíticas.

### PRINCIPAIS MUDANÇAS

**Dados:**
- Bronze: Fed + Selic (2 variáveis, 247 obs)
- Prata: **Fed + Selic + Inflação + Atividade** (4 variáveis, 250+ obs)

**Modelos:**
- Bronze: LP(2) + BVAR(2)
- Prata: **Small BVAR(4)** + LP(4) com Minnesota/Observables priors

**Forecasts:**
- Bronze: Cenários simples
- Prata: **Conditional forecasts** com avaliação de efficiency gain

**Inovação:**
- Prata: **Geração de cenários via IA** (LLM → paths quantitativos)

---

## 📊 EXPANSÃO DE DADOS (Semanas 6-7)

### Fontes Adicionais

**Brasil (BCB/SGS):**
```python
{
  "ipca_mensal": {
    "serie": 433,
    "frequencia": "mensal",
    "transformacao": "YoY % change"
  },
  "ipca_12m": {
    "serie": 13,
    "frequencia": "mensal",
    "uso": "direto"
  },
  "ibc_br": {
    "serie": 24363,
    "frequencia": "mensal",
    "transformacao": "YoY % change dessazonalizado"
  },
  "pib_trimestral": {
    "serie": 4380,
    "frequencia": "trimestral",
    "interpolacao": "cubic spline → mensal"
  }
}
```

**Estados Unidos (FRED):**
```python
{
  "cpi_all_urban": {
    "serie": "CPIAUCSL",
    "frequencia": "mensal",
    "transformacao": "YoY % change"
  },
  "gdp": {
    "serie": "GDP",
    "frequencia": "trimestral",
    "interpolacao": "cubic spline → mensal"
  },
  "desemprego": {
    "serie": "UNRATE",
    "frequencia": "mensal",
    "uso": "variável controle opcional"
  }
}
```

### Pipeline de Ingestão

**Arquivo:** `src/data/ingestion/multivariate_pipeline.py`

```python
class MultivariateDataPipeline:
    """
    Pipeline para ingestão de dados multivariados
    
    Bronze: 2 variáveis (Fed, Selic)
    Prata:  4 variáveis (Fed, Selic, Inflation, Activity)
    """
    
    def fetch_brazil_data(self) -> pd.DataFrame:
        """Buscar dados do Brasil (BCB/SGS)"""
        # IPCA 12M
        ipca = fetch_bcb_series(433, start='2005-01-01')
        
        # IBC-Br dessazonalizado YoY
        ibc_br = fetch_bcb_series(24363, start='2005-01-01')
        ibc_br_yoy = ibc_br.pct_change(12) * 100
        
        # PIB trimestral → mensal
        pib_tri = fetch_bcb_series(4380, start='2005-01-01')
        pib_mensal = interpolate_quarterly_to_monthly(pib_tri, method='cubic')
        
        return pd.DataFrame({
            'selic': fetch_selic(),
            'ipca_12m': ipca,
            'activity_ibc': ibc_br_yoy,
            'activity_pib': pib_mensal
        })
    
    def fetch_us_data(self) -> pd.DataFrame:
        """Buscar dados dos EUA (FRED)"""
        # CPI YoY
        cpi = fetch_fred_series('CPIAUCSL', start='2005-01-01')
        cpi_yoy = cpi.pct_change(12) * 100
        
        # GDP trimestral → mensal
        gdp_tri = fetch_fred_series('GDP', start='2005-01-01')
        gdp_mensal = interpolate_quarterly_to_monthly(gdp_tri, method='cubic')
        
        return pd.DataFrame({
            'fed_rate': fetch_fred_series('FEDFUNDS'),
            'cpi_yoy': cpi_yoy,
            'activity_gdp': gdp_mensal
        })
    
    def merge_and_validate(self, brazil_df, us_df) -> pd.DataFrame:
        """Mesclar dados e validar qualidade"""
        # Merge por index (datas)
        combined = pd.merge(
            brazil_df, us_df, 
            left_index=True, right_index=True, 
            how='inner'
        )
        
        # Validações
        assert len(combined) >= 200, "N muito pequeno após merge"
        assert combined.isnull().sum().sum() < len(combined) * 0.05, "Muitos NaNs"
        
        # Selecionar variáveis finais
        final = combined[[
            'fed_rate', 'selic', 
            'ipca_12m', 'activity_ibc'  # ou activity_pib
        ]].copy()
        
        final.columns = ['fed_rate', 'selic', 'inflation', 'activity']
        
        return final
```

### Validação de Qualidade Expandida

**Arquivo:** `tests/data_quality/test_multivariate_data.py`

```python
def test_inflation_stationarity():
    """IPCA 12M deve ser I(0) ou I(1) suave"""
    ipca = load_ipca_12m()
    
    # ADF test
    adf_pval = adfuller(ipca.dropna())[1]
    
    # Se não estacionário, diferenciar
    if adf_pval > 0.05:
        d_ipca = ipca.diff().dropna()
        adf_pval_diff = adfuller(d_ipca)[1]
        assert adf_pval_diff < 0.05, "IPCA não estacionário nem em diferenças"

def test_activity_yoy_stationarity():
    """IBC-Br YoY deve ser I(0)"""
    ibc_yoy = load_ibc_br_yoy()
    adf_pval = adfuller(ibc_yoy.dropna())[1]
    assert adf_pval < 0.10, "IBC-Br YoY não estacionário"

def test_data_alignment():
    """Todas as 4 séries devem estar alinhadas temporalmente"""
    data = load_multivariate_data()
    
    # Sem NaNs após merge
    assert data.isnull().sum().sum() == 0
    
    # Período comum >= 200 obs
    assert len(data) >= 200
```

---

## 🤖 SMALL BVAR(4) (Semanas 8-9)

### Implementação

**Arquivo:** `src/models/bvar_small.py`

```python
class SmallBVAR(BVARMinnesota):
    """
    Small BVAR(4) com Minnesota Prior
    
    Extensão de BVARMinnesota para 4 variáveis:
    Y_t = [Fed, Selic, Inflation, Activity]'
    """
    
    def __init__(
        self,
        n_vars: int = 4,          # 4 variáveis agora
        n_lags: int = 2,
        lambda1: float = 0.2,     # Shrinkage geral
        lambda2: float = 0.4,     # Cross-equation
        lambda3: float = 1.5,     # Lag decay
        **kwargs
    ):
        super().__init__(
            n_vars=n_vars,
            n_lags=n_lags,
            lambda1=lambda1,
            lambda2=lambda2,
            lambda3=lambda3,
            **kwargs
        )
    
    def structural_irfs_expanded(
        self,
        horizon: int = 12,
        shock_var: int = 0,  # Fed
        response_vars: List[int] = [1, 2, 3]  # Selic, Inflation, Activity
    ) -> Dict[str, np.ndarray]:
        """
        IRFs estruturais com Cholesky
        
        Ordenação: Fed → Inflation → Activity → Selic
        """
        # Decomposição de Cholesky
        L = np.linalg.cholesky(self.sigma)
        
        # IRFs estruturais
        irfs = {}
        for resp_var in response_vars:
            irf = self._compute_irf(
                shock_var=shock_var,
                response_var=resp_var,
                horizon=horizon,
                structural=True,
                cholesky_factor=L
            )
            
            var_names = ['fed', 'selic', 'inflation', 'activity']
            irfs[f"{var_names[shock_var]}_to_{var_names[resp_var]}"] = irf
        
        return irfs
    
    def variance_decomposition(
        self,
        horizon: int = 12
    ) -> Dict[str, pd.DataFrame]:
        """
        Decomposição da variância do erro de previsão
        
        Retorna contribuição de cada choque para variância
        de cada variável em cada horizonte
        """
        # Implementação via IRFs estruturais
        # ...
        pass
```

### Calibração de Priors

**Arquivo:** `scripts/calibrate_priors_prata.py`

```python
def calibrate_minnesota_priors():
    """
    Calibrar λ1, λ2, λ3 para Small BVAR(4)
    
    Método: Grid search com cross-validation
    """
    data = load_multivariate_data()
    
    # Grid de hiperparâmetros
    lambda1_grid = [0.1, 0.15, 0.2, 0.25, 0.3]
    lambda2_grid = [0.3, 0.4, 0.5]
    lambda3_grid = [1.0, 1.5, 2.0]
    
    best_params = None
    best_score = np.inf
    
    for l1, l2, l3 in product(lambda1_grid, lambda2_grid, lambda3_grid):
        # Time-series cross-validation
        scores = []
        for train, test in rolling_origin_cv(data, horizon=6, n_splits=10):
            model = SmallBVAR(
                lambda1=l1, lambda2=l2, lambda3=l3
            )
            model.fit(train)
            
            # Forecast
            fc = model.forecast(horizon=6)
            
            # Score: CRPS médio
            crps = continuous_ranked_probability_score(fc, test['selic'])
            scores.append(crps)
        
        avg_score = np.mean(scores)
        
        if avg_score < best_score:
            best_score = avg_score
            best_params = (l1, l2, l3)
    
    logger.info(f"Best params: λ1={best_params[0]}, λ2={best_params[1]}, λ3={best_params[2]}")
    logger.info(f"Best CRPS: {best_score:.2f}")
    
    return best_params
```

### Testes Científicos

**Arquivo:** `tests_scientific/small_bvar/test_small_bvar.py`

```python
def test_stability_small_bvar():
    """Small BVAR(4) deve ser estável"""
    data = load_multivariate_data()
    
    model = SmallBVAR(n_vars=4, n_lags=2)
    model.fit(data)
    
    # Verificar eigenvalues
    assert model.stable, "Modelo instável!"
    assert np.max(np.abs(model.eigs_F)) < 1.0
    assert np.max(np.abs(model.eigs_F)) < 0.99, "Próximo da instabilidade"

def test_irfs_cointegrated():
    """IRFs devem convergir para zero"""
    model = load_trained_small_bvar()
    
    irfs = model.structural_irfs_expanded(horizon=24)
    
    # Verificar convergência
    for irf_name, irf_values in irfs.items():
        # Últimos 6 valores devem ser próximos de zero
        assert np.abs(irf_values[-6:]).max() < 0.1, \
            f"IRF {irf_name} não converge"

def test_variance_decomposition_sums_to_one():
    """Decomposição deve somar 100% em cada horizonte"""
    model = load_trained_small_bvar()
    
    vd = model.variance_decomposition(horizon=12)
    
    for var_name, vd_df in vd.items():
        # Soma por horizonte deve ser 1.0
        for h in range(12):
            total = vd_df.iloc[h].sum()
            assert np.abs(total - 1.0) < 1e-6, \
                f"{var_name} h={h}: soma={total} != 1.0"
```

---

## 📈 FORECASTS CONDICIONAIS (Semanas 10-11)

### Método Waggoner-Zha

**Arquivo:** `src/models/conditional_forecasting.py`

```python
class ConditionalForecaster:
    """
    Forecasts condicionais via Waggoner-Zha
    
    Dado path do Fed, gerar distribuição preditiva da Selic
    condicionada ao path.
    """
    
    def __init__(self, bvar_model: SmallBVAR):
        self.bvar = bvar_model
    
    def conditional_forecast(
        self,
        fed_path: List[float],
        horizon: int = 12,
        n_simulations: int = 5000
    ) -> Dict[str, np.ndarray]:
        """
        Forecast condicional dado path do Fed
        
        Args:
            fed_path: Path do Fed para horizontes 1-H
            horizon: Horizonte máximo
            n_simulations: Simulações Monte Carlo
        
        Returns:
            Dict com mean, std, quantiles da Selic condicionada
        """
        # Unconditional forecast (baseline)
        uncond = self.bvar.forecast(horizon=horizon, n_simulations=n_simulations)
        
        # Conditional forecast (impor path do Fed)
        cond_sims = []
        
        for sim in range(n_simulations):
            # Simular path completo de Y_t
            y_sim = self._simulate_path(horizon)
            
            # Se path do Fed está dentro de tolerância, aceitar
            if self._check_path_consistency(y_sim[:, 0], fed_path, tol=0.1):
                cond_sims.append(y_sim[:, 1])  # Selic
        
        # Se poucos aceitos, usar método de otimização
        if len(cond_sims) < 100:
            cond_sims = self._optimize_conditional_path(fed_path, horizon)
        
        cond_sims = np.array(cond_sims)
        
        return {
            'mean': cond_sims.mean(axis=0),
            'std': cond_sims.std(axis=0),
            'ci95_lower': np.percentile(cond_sims, 2.5, axis=0),
            'ci95_upper': np.percentile(cond_sims, 97.5, axis=0),
            'unconditional_mean': uncond['mean'],
            'efficiency_gain': self._compute_efficiency_gain(cond_sims, uncond)
        }
    
    def _compute_efficiency_gain(
        self,
        cond_sims: np.ndarray,
        uncond_fc: Dict
    ) -> float:
        """
        Efficiency gain = 1 - (Var_cond / Var_uncond)
        
        Quanto maior, melhor o forecast condicional
        """
        var_cond = cond_sims.var(axis=0).mean()
        var_uncond = uncond_fc['std']**2
        
        return 1.0 - (var_cond / var_uncond)
```

### Backtesting Conditional vs Unconditional

**Arquivo:** `tests/backtests/test_conditional_accuracy.py`

```python
def test_conditional_forecast_accuracy():
    """
    Forecasts condicionais devem ter efficiency gain ≥ 10%
    """
    model = load_trained_small_bvar()
    
    # Backtesting histórico
    data = load_multivariate_data()
    
    results = []
    
    for t in range(150, len(data) - 12):
        # Train até t
        train = data.iloc[:t]
        test = data.iloc[t:t+12]
        
        # Re-estimar
        model.fit(train)
        
        # Unconditional forecast
        uncond = model.forecast(horizon=12)
        
        # Conditional forecast (path real do Fed)
        fed_path = test['fed_rate'].tolist()
        cond = model.conditional_forecast(fed_path=fed_path, horizon=12)
        
        # Avaliar
        rmse_cond = np.sqrt(np.mean((cond['mean'] - test['selic'])**2))
        rmse_uncond = np.sqrt(np.mean((uncond['mean'] - test['selic'])**2))
        
        efficiency = 1.0 - (rmse_cond / rmse_uncond)
        
        results.append({
            'date': test.index[0],
            'rmse_conditional': rmse_cond,
            'rmse_unconditional': rmse_uncond,
            'efficiency_gain': efficiency
        })
    
    # Agregação
    avg_efficiency = np.mean([r['efficiency_gain'] for r in results])
    
    # GATE: efficiency gain ≥ 10%
    assert avg_efficiency >= 0.10, \
        f"Efficiency gain {avg_efficiency:.2%} < 10%"
    
    logger.info(f"✅ Conditional forecasts: efficiency gain = {avg_efficiency:.2%}")
```

---

## 🤖 GERAÇÃO DE CENÁRIOS VIA IA (Semanas 14-15 - Opcional)

### Integração com LLM

**Arquivo:** `src/ai/scenario_generator.py`

```python
from openai import OpenAI
import anthropic

class AIScenarioGenerator:
    """
    Gerador de cenários econômicos via LLM
    
    Input: Narrativa econômica (texto livre)
    Output: Path quantitativo do Fed (12 meses)
    """
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.client = OpenAI() if provider == "openai" else anthropic.Anthropic()
    
    def generate_fed_path_from_narrative(
        self,
        narrative: str,
        current_fed_rate: float = 5.33,
        horizon: int = 12
    ) -> Dict[str, Any]:
        """
        Gerar path do Fed a partir de narrativa econômica
        
        Args:
            narrative: Texto descrevendo cenário econômico
            current_fed_rate: Taxa atual do Fed
            horizon: Meses à frente
        
        Returns:
            Dict com fed_path, confidence, metadata
        """
        prompt = f"""
Você é um economista quantitativo. Dado o cenário econômico abaixo, 
traduza-o em um path plausível da taxa de juros do Fed para os 
próximos {horizon} meses.

CENÁRIO:
{narrative}

TAXA ATUAL DO FED: {current_fed_rate}%

INSTRUÇÕES:
1. Retorne path mensal em bps (múltiplos de 25)
2. Mantenha plausibilidade econômica (mudanças graduais)
3. Justifique cada movimento
4. Indique nível de confiança (low/medium/high)

FORMATO DE SAÍDA (JSON):
{{
  "fed_path_bps": [5.33, 5.08, 4.83, ...],  // 12 valores
  "rationale": "Gradual loosening devido a...",
  "confidence": "medium",
  "key_assumptions": ["inflação controlada", "crescimento moderado"],
  "severity_check": "plausible"  // severe_but_plausible | implausible
}}
"""
        
        # Chamar LLM
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
        else:
            # Anthropic Claude
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            result = json.loads(response.content[0].text)
        
        # Validações
        validated = self._validate_and_sanitize(result, current_fed_rate, horizon)
        
        return validated
    
    def _validate_and_sanitize(
        self,
        llm_output: Dict,
        current_rate: float,
        horizon: int
    ) -> Dict:
        """
        Validar output do LLM e sanitizar
        
        Regras "severe but plausible":
        - Mudanças graduais (max 50 bps/mês)
        - Range total razoável (0% - 8%)
        - Sem descontinuidades abruptas
        """
        fed_path = llm_output.get('fed_path_bps', [])
        
        # Validação 1: tamanho correto
        if len(fed_path) != horizon:
            raise ValueError(f"Path com {len(fed_path)} != {horizon} meses")
        
        # Validação 2: múltiplos de 25
        for rate in fed_path:
            if (rate * 100) % 25 != 0:
                # Arredondar para múltiplo de 25
                fed_path = [round(r * 4) / 4 for r in fed_path]
                break
        
        # Validação 3: mudanças graduais (max 50 bps/mês)
        for i in range(len(fed_path) - 1):
            delta = abs(fed_path[i+1] - fed_path[i]) * 100
            if delta > 50:
                raise ValueError(f"Mudança abrupta: {delta} bps no mês {i+1}")
        
        # Validação 4: range razoável
        if min(fed_path) < 0 or max(fed_path) > 8.0:
            raise ValueError(f"Path fora do range [0%, 8%]: {min(fed_path)}-{max(fed_path)}")
        
        # Adicionar metadata
        llm_output['llm_provider'] = self.provider
        llm_output['llm_model'] = "gpt-4" if self.provider == "openai" else "claude-3-sonnet"
        llm_output['validated'] = True
        llm_output['timestamp'] = datetime.utcnow().isoformat()
        
        return llm_output
```

### Endpoint Expandido

**Adicionar a:** `src/api/endpoints/prediction.py`

```python
@router.post("/selic-from-fed/scenario-ai")
async def predict_from_ai_scenario(
    narrative: str = Body(..., description="Narrativa econômica"),
    current_fed_rate: float = Body(5.33, description="Taxa atual do Fed"),
    horizon: int = Body(12, ge=1, le=24),
    auth_headers = Depends(get_auth_headers)
):
    """
    Previsão de Selic a partir de narrativa econômica (via IA)
    
    BETA: Usa LLM para traduzir narrativa → path do Fed → previsão Selic
    """
    try:
        # Gerar path via IA
        ai_generator = AIScenarioGenerator(provider="openai")
        
        ai_result = ai_generator.generate_fed_path_from_narrative(
            narrative=narrative,
            current_fed_rate=current_fed_rate,
            horizon=horizon
        )
        
        # Usar path para forecast condicional
        prediction_service = get_prediction_service()
        
        forecast = prediction_service.predict_conditional(
            fed_path=ai_result['fed_path_bps'],
            horizon=horizon
        )
        
        # Adicionar metadata da IA
        forecast['ai_metadata'] = {
            'narrative': narrative,
            'llm_provider': ai_result['llm_provider'],
            'llm_model': ai_result['llm_model'],
            'confidence': ai_result['confidence'],
            'key_assumptions': ai_result['key_assumptions'],
            'severity_check': ai_result['severity_check']
        }
        
        return forecast
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar cenário via IA: {str(e)}"
        )
```

---

## 🎯 GATE DE PROMOÇÃO (Semanas 12-13)

### Configuração de Thresholds

**Arquivo:** `configs/gate_thresholds.json`

```json
{
  "version": "1.0",
  "gates": {
    "stability": {
      "max_eigenvalue": 0.99,
      "required": true
    },
    "coverage": {
      "ci95_min": 0.90,
      "ci68_min": 0.65,
      "required": true
    },
    "calibration": {
      "pit_uniformity_pval_min": 0.05,
      "required": true
    },
    "accuracy": {
      "crps_max": 20.0,
      "brier_score_max": 0.25,
      "required": true
    },
    "conditional_efficiency": {
      "efficiency_gain_min": 0.10,
      "required": true,
      "applies_to": ["v2.0.0+"]
    },
    "data_quality": {
      "n_observations_min": 200,
      "max_missing_pct": 0.05,
      "required": true
    }
  },
  "manual_override_allowed": true,
  "override_requires_justification": true
}
```

### Implementação do Gate

**Arquivo:** `src/validation/promotion_gate.py`

```python
class PromotionGate:
    """
    Gate de promoção de modelos
    
    Valida se modelo atende thresholds antes de ir para produção
    """
    
    def __init__(self, config_path: str = "configs/gate_thresholds.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        self.gates = self.config['gates']
    
    def evaluate(
        self,
        model_version: str,
        backtest_results: Dict[str, float],
        model_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Avaliar se modelo passa nos gates
        
        Returns:
            Dict com passed, failed_gates, warnings
        """
        failed_gates = []
        warnings = []
        
        # Gate 1: Stability
        if self.gates['stability']['required']:
            max_eig = model_metadata.get('max_eigenvalue', 1.0)
            if max_eig >= self.gates['stability']['max_eigenvalue']:
                failed_gates.append({
                    'gate': 'stability',
                    'value': max_eig,
                    'threshold': self.gates['stability']['max_eigenvalue'],
                    'message': 'Modelo próximo da instabilidade'
                })
        
        # Gate 2: Coverage
        if self.gates['coverage']['required']:
            coverage = backtest_results.get('coverage_ci95', 0.0)
            if coverage < self.gates['coverage']['ci95_min']:
                failed_gates.append({
                    'gate': 'coverage',
                    'value': coverage,
                    'threshold': self.gates['coverage']['ci95_min'],
                    'message': f'Cobertura CI95 {coverage:.2%} < {self.gates["coverage"]["ci95_min"]:.0%}'
                })
        
        # Gate 3: Calibration
        if self.gates['calibration']['required']:
            pit_pval = backtest_results.get('pit_uniformity_pval', 0.0)
            if pit_pval < self.gates['calibration']['pit_uniformity_pval_min']:
                failed_gates.append({
                    'gate': 'calibration',
                    'value': pit_pval,
                    'threshold': self.gates['calibration']['pit_uniformity_pval_min'],
                    'message': 'PIT test falhou (não uniforme)'
                })
        
        # Gate 4: Accuracy
        if self.gates['accuracy']['required']:
            crps = backtest_results.get('crps', 999)
            if crps > self.gates['accuracy']['crps_max']:
                failed_gates.append({
                    'gate': 'accuracy',
                    'value': crps,
                    'threshold': self.gates['accuracy']['crps_max'],
                    'message': f'CRPS {crps:.2f} > {self.gates["accuracy"]["crps_max"]}'
                })
        
        # Gate 5: Conditional Efficiency (Prata)
        gate_cond = self.gates['conditional_efficiency']
        if (gate_cond['required'] and 
            any(model_version >= v for v in gate_cond['applies_to'])):
            
            eff_gain = backtest_results.get('conditional_efficiency_gain', 0.0)
            if eff_gain < gate_cond['efficiency_gain_min']:
                failed_gates.append({
                    'gate': 'conditional_efficiency',
                    'value': eff_gain,
                    'threshold': gate_cond['efficiency_gain_min'],
                    'message': f'Efficiency gain {eff_gain:.2%} < 10%'
                })
        
        # Resultado
        passed = len(failed_gates) == 0
        
        return {
            'passed': passed,
            'failed_gates': failed_gates,
            'warnings': warnings,
            'manual_override_allowed': self.config['manual_override_allowed'],
            'evaluated_at': datetime.utcnow().isoformat()
        }
```

### Teste do Gate

**Arquivo:** `tests/unit/test_promotion_gate.py`

```python
def test_gate_rejects_unstable_model():
    """Gate deve rejeitar modelo instável"""
    gate = PromotionGate()
    
    # Modelo com max eigenvalue = 1.05 (INSTÁVEL)
    result = gate.evaluate(
        model_version="v2.0.0",
        backtest_results={'coverage_ci95': 0.95, 'crps': 15.0},
        model_metadata={'max_eigenvalue': 1.05}
    )
    
    assert not result['passed']
    assert any(g['gate'] == 'stability' for g in result['failed_gates'])

def test_gate_rejects_low_coverage():
    """Gate deve rejeitar modelo com cobertura baixa"""
    gate = PromotionGate()
    
    result = gate.evaluate(
        model_version="v2.0.0",
        backtest_results={'coverage_ci95': 0.85, 'crps': 15.0},  # < 90%
        model_metadata={'max_eigenvalue': 0.4}
    )
    
    assert not result['passed']
    assert any(g['gate'] == 'coverage' for g in result['failed_gates'])

def test_gate_accepts_good_model():
    """Gate deve aceitar modelo que atende todos os thresholds"""
    gate = PromotionGate()
    
    result = gate.evaluate(
        model_version="v2.0.0",
        backtest_results={
            'coverage_ci95': 0.94,
            'pit_uniformity_pval': 0.42,
            'crps': 12.1,
            'brier_score': 0.14,
            'conditional_efficiency_gain': 0.18
        },
        model_metadata={
            'max_eigenvalue': 0.41,
            'n_observations': 250
        }
    )
    
    assert result['passed']
    assert len(result['failed_gates']) == 0
```

---

## 📊 MÉTRICAS EXPANDIDAS (API Response)

### Response com Métricas de Qualidade

```json
{
  "expected_move_bps": 18,
  "horizon_months": "1-3",
  "distribution": [...],
  "per_meeting": [...],
  "model_metadata": {
    "version": "v2.0.0",
    "variables": ["fed_rate", "selic", "inflation", "activity"],
    "methodology": "Small BVAR(4) with Minnesota prior",
    "backtest_metrics": {
      "coverage_ci95": 0.94,
      "crps": 12.1,
      "conditional_efficiency_gain": 0.18
    }
  },
  "forecast_quality": {
    "conditional": true,
    "efficiency_gain_vs_unconditional": 0.18,
    "coverage_rate_ci95": 0.94,
    "calibration_score": 0.89
  },
  "variance_decomposition": {
    "fed_contribution_pct": 45,
    "inflation_contribution_pct": 35,
    "activity_contribution_pct": 20
  },
  "rationale_expanded": "Small BVAR(4) indica resposta positiva da Selic (+18 bps esperado em 3 meses) ao choque de +25 bps do Fed. Inflação contribui 35% da variância do erro de previsão, atividade 20%, Fed 45%. Forecast condicional 18% mais preciso que incondicional."
}
```

---

## 🎯 DELIVERABLES PRATA (Checklist)

### Dados (Semanas 6-7)

- [ ] Pipeline de ingestão BCB/FRED expandido
- [ ] 4 séries temporais integradas (Fed, Selic, Inflation, Activity)
- [ ] Interpolação trimestral→mensal validada
- [ ] N ≥ 200 observações alinhadas
- [ ] Testes de estacionariedade aprovados
- [ ] Data hash SHA-256 atualizado

### Modelos (Semanas 8-9)

- [ ] SmallBVAR(4) implementado
- [ ] Priors calibrados por cross-validation
- [ ] Estabilidade verificada (eigenvalues < 1.0)
- [ ] IRFs estruturais expandidos (Fed→Selic, Fed→Inflation, Fed→Activity)
- [ ] Variance decomposition implementada
- [ ] Testes científicos do small VAR passando

### Forecasts Condicionais (Semanas 10-11)

- [ ] Método Waggoner-Zha implementado
- [ ] 20+ cenários canônicos gerados
- [ ] Backtesting conditional vs unconditional
- [ ] Efficiency gain ≥ 10% validado
- [ ] Coverage CI95 ≥ 92%
- [ ] PIT uniformity p-value ≥ 0.05

### Gate e Promoção (Semanas 12-13)

- [ ] `gate_thresholds.json` criado
- [ ] `PromotionGate` implementado
- [ ] Testes de gate passando (aceita/rejeita corretamente)
- [ ] Canary deployment de v2.0.0
- [ ] Monitoramento de métricas de produção
- [ ] Promoção ou rollback decidido

### IA (Semanas 14-15 - Opcional)

- [ ] `AIScenarioGenerator` implementado
- [ ] Integração OpenAI/Anthropic
- [ ] Validador "severe but plausible"
- [ ] Endpoint `/scenario-ai` funcional
- [ ] Testes de coerência econômica
- [ ] Logs de metadata (prompt, LLM usado)

### Documentação

- [ ] Model Card v2.0.0 completo
- [ ] README atualizado com Prata
- [ ] API_README com novos endpoints
- [ ] Relatório de backtesting expandido
- [ ] Guia de geração de cenários via IA

---

## 🏆 CRITÉRIOS DE ACEITAÇÃO PRATA

### Funcional

- [ ] Small BVAR(4) em produção
- [ ] Forecasts condicionais com efficiency gain ≥ 10%
- [ ] Variance decomposition disponível na API
- [ ] Cenários via IA funcionais (beta)
- [ ] Fallback robusto se IA falhar

### Não-Funcional

- [ ] P95 latência < 300 ms (small VAR mais pesado)
- [ ] Coverage CI95 ≥ 92%
- [ ] CRPS ≤ 18.0
- [ ] PIT uniformity p-value ≥ 0.05
- [ ] Disponibilidade ≥ 99.95% mensal
- [ ] Tempo de re-treino < 30 minutos

### Qualidade

- [ ] Testes expandidos (conditional, gate, AI)
- [ ] Coverage ≥ 75% (com novos módulos)
- [ ] Types estritos mantidos
- [ ] Error handling robusto em IA

### Documentação

- [ ] Model Cards v2.0
- [ ] Relatórios de backtesting completos
- [ ] Guias de uso de cenários via IA
- [ ] Runbook atualizado

---

## 📅 TIMELINE DETALHADO

```
Semanas 1-5:  ✅ BRONZE COMPLETO
Semanas 6-7:  📊 Expansão de Dados
Semanas 8-9:  🤖 Small BVAR(4)
Semanas 10-11: 📈 Forecasts Condicionais
Semanas 12-13: 🎯 Gate e Promoção
Semanas 14-15: 🤖 IA (Opcional)

TOTAL: 10-15 semanas (30-60 dias)
```

---

**🥈 PRATA: SISTEMA ANALÍTICO ROBUSTO COM IA! 🥈**

**Ready to scale to full internal use!** 🚀

