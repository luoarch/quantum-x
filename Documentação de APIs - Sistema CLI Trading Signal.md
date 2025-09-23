<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Documentação de APIs - Sistema CLI Trading Signal Generator

## 1. API do Banco Central do Brasil (SGS - Sistema Gerenciador de Séries Temporais)

### Base URL

```
https://api.bcb.gov.br/dados/serie/bcdata.sgs
```


### Endpoint Principal

```
GET /{codigo_serie}/dados?formato={formato}&limite={limite}&dataInicial={data}&dataFinal={data}
```


### Séries Principais para CLI

| Indicador | Código | Descrição | Frequência |
| :-- | :-- | :-- | :-- |
| IPCA | 433 | Índice de Preços ao Consumidor Amplo (% a.m.) | Mensal |
| SELIC | 432 | Taxa Selic (% a.a.) | Mensal |
| Câmbio | 1 | Taxa de câmbio - R$/US$ - comercial - compra - média | Diária |
| Produção Industrial | 21859 | Produção industrial - geral - índice (2012=100) | Mensal |
| PIB Mensal | 4380 | PIB mensal - valores correntes (R\$ milhões) | Mensal |
| Taxa Desemprego | 24369 | Taxa de desocupação - total | Trimestral |

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
| :-- | :-- | :-- | :-- |
| formato | string | Não | `json` ou `xml` (padrão: json) |
| limite | integer | Não | Número máximo de observações |
| dataInicial | string | Não | Data inicial (dd/mm/aaaa) |
| dataFinal | string | Não | Data final (dd/mm/aaaa) |

### Exemplo de Uso

```python
import requests
import pandas as pd

def fetch_bcb_data(series_code, limit=100):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs/{series_code}/dados"
    params = {
        'formato': 'json',
        'limite': limit
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data:  # Verificar se retornou dados
        df = pd.DataFrame(data)
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        return df
    return pd.DataFrame()

# Coletar dados principais
ipca = fetch_bcb_data(433, 60)      # IPCA últimos 60 meses
selic = fetch_bcb_data(432, 60)     # SELIC últimos 60 meses
cambio = fetch_bcb_data(1, 252)     # Câmbio último ano (252 dias úteis)
```


### Formato de Resposta (JSON)

```json
[
    {
        "data": "01/09/2025",
        "valor": "0.18"
    },
    {
        "data": "01/08/2025", 
        "valor": "0.23"
    }
]
```


## 2. API OECD SDMX (Statistical Data and Metadata eXchange)

### Base URL

```
https://stats.oecd.org/restsdmx/sdmx.ashx
```


### Endpoint CLI

```
GET /GetData/CLI/{frequency}.{country}/all?startTime={year}&endTime={year}&detail=Full&dimensionAtObservation=AllDimensions
```


### Países Disponíveis

| País | Código | CLI Disponível |
| :-- | :-- | :-- |
| Brasil | BRA | Sim |
| Estados Unidos | USA | Sim |
| China | CHN | Sim |
| Zona Euro | EA19 | Sim |
| OECD Total | OECD | Sim |
| Alemanha | DEU | Sim |
| Reino Unido | GBR | Sim |

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
| :-- | :-- | :-- | :-- |
| frequency | string | Sim | M (mensal), Q (trimestral) |
| country | string | Sim | Código do país (BRA, USA, etc.) |
| startTime | integer | Não | Ano inicial (ex: 2020) |
| endTime | integer | Não | Ano final (ex: 2025) |
| detail | string | Não | Full, DataOnly, SeriesKeysOnly |

### Exemplo de Uso

```python
import requests
import pandas as pd
import xml.etree.ElementTree as ET

def fetch_oecd_cli(country='BRA', start_year=2020, end_year=2025):
    url = (
        f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/CLI/M.{country}/all?"
        f"startTime={start_year}&endTime={end_year}&detail=Full&"
        "dimensionAtObservation=AllDimensions"
    )
    
    response = requests.get(url)
    
    if response.status_code == 200:
        # Parse XML SDMX
        root = ET.fromstring(response.text)
        
        observations = []
        for series in root.findall('.//Series'):
            for obs in series.findall('Obs'):
                time_elem = obs.find('TimePeriod')
                value_elem = obs.find('ObsValue')
                
                if time_elem is not None and value_elem is not None:
                    time_period = time_elem.text
                    value = float(value_elem.attrib['value'])
                    
                    observations.append({
                        'TimePeriod': time_period,
                        'CLI': value,
                        'Country': country
                    })
        
        if observations:
            df = pd.DataFrame(observations)
            # Converter YYYY-MM para datetime
            df['Date'] = pd.to_datetime(df['TimePeriod'] + '-01')
            return df.sort_values('Date')
    
    return pd.DataFrame()

# Coletar CLI para múltiplos países
cli_brasil = fetch_oecd_cli('BRA')
cli_eua = fetch_oecd_cli('USA') 
cli_global = fetch_oecd_cli('OECD')
```


### Formato de Resposta (SDMX-ML)

```xml
<Series>
    <Obs>
        <TimePeriod>2025-08</TimePeriod>
        <ObsValue value="99.8"/>
    </Obs>
    <Obs>
        <TimePeriod>2025-07</TimePeriod>
        <ObsValue value="100.2"/>
    </Obs>
</Series>
```


## 3. Classe Unificada para Coleta de Dados

```python
class EconomicDataCollector:
    def __init__(self):
        self.bcb_base = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
        self.oecd_base = "https://stats.oecd.org/restsdmx/sdmx.ashx"
        
        # Mapeamento de séries BCB
        self.bcb_series = {
            'ipca': 433,
            'selic': 432,
            'cambio': 1,
            'prod_industrial': 21859,
            'pib_mensal': 4380
        }
    
    def get_bcb_indicator(self, indicator, months=60):
        """Coleta indicador do BCB"""
        series_code = self.bcb_series.get(indicator)
        if not series_code:
            raise ValueError(f"Indicador {indicator} não encontrado")
        
        return fetch_bcb_data(series_code, months)
    
    def get_cli_data(self, countries=['BRA', 'USA', 'OECD'], years=5):
        """Coleta CLI OECD para múltiplos países"""
        current_year = pd.Timestamp.now().year
        start_year = current_year - years
        
        all_cli = []
        for country in countries:
            df = fetch_oecd_cli(country, start_year, current_year)
            if not df.empty:
                all_cli.append(df)
        
        if all_cli:
            return pd.concat(all_cli, ignore_index=True)
        return pd.DataFrame()
    
    def get_all_data(self):
        """Coleta completa de dados para CLI"""
        data = {}
        
        # Dados BCB
        for indicator in self.bcb_series.keys():
            try:
                data[indicator] = self.get_bcb_indicator(indicator)
                print(f"✅ {indicator}: {len(data[indicator])} registros")
            except Exception as e:
                print(f"❌ Erro ao coletar {indicator}: {e}")
        
        # CLI OECD
        try:
            data['cli'] = self.get_cli_data()
            print(f"✅ CLI OECD: {len(data['cli'])} registros")
        except Exception as e:
            print(f"❌ Erro ao coletar CLI: {e}")
        
        return data

# Uso prático
collector = EconomicDataCollector()
all_data = collector.get_all_data()

# Salvar dados
for name, df in all_data.items():
    if not df.empty:
        df.to_csv(f'{name}_data.csv', index=False)
```


## 4. Tratamento de Erros e Limitações

### Rate Limits

- **BCB**: Sem limite oficial documentado, mas recomendado não exceder 100 req/min
- **OECD**: Sem limite oficial, mas timeout após 30 segundos


### Códigos de Erro Comuns

| API | Código | Descrição | Solução |
| :-- | :-- | :-- | :-- |
| BCB | 400 | Série inexistente | Verificar código da série |
| BCB | 404 | Dados não encontrados | Ajustar período de consulta |
| OECD | 500 | Erro interno | Tentar novamente após alguns minutos |
| OECD | Timeout | Requisição muito longa | Reduzir período de consulta |

### Exemplo de Tratamento

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Uso com retry automático
session = create_session_with_retries()
response = session.get(url, timeout=30)
```

Esta documentação fornece uma base sólida para integração das APIs no seu sistema CLI Trading Signal Generator.

