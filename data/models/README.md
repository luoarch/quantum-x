# 📦 Modelos Treinados

Este diretório contém os artefatos versionados dos modelos FED-Selic.

## Estrutura

```
data/models/
├── v1.0.0/
│   ├── model_lp.pkl          # Local Projections treinado
│   ├── model_bvar.pkl         # BVAR Minnesota treinado
│   ├── irfs_lp.json           # IRFs do LP
│   ├── irfs_bvar.json         # IRFs estruturais do BVAR
│   └── metadata.json          # Metadata com hash, métricas, etc.
├── v1.1.0/
│   └── ...
└── README.md                  # Este arquivo
```

## Geração de Modelos

Para treinar uma nova versão:

```bash
python scripts/train_pipeline.py --version v1.x.x
```

## Metadata Exemplo (v1.0.0)

```json
{
  "version": "v1.0.0",
  "created_at": "2025-09-30T19:35:35.015824Z",
  "data_hash": "sha256:60b22b647ec37a53432a0c5b0534f85a574d47ac117db56d14be15b28bfaf1d3",
  "methodology": "LP primary, BVAR fallback",
  "n_observations": 246,
  "models": {
    "local_projections": {
      "n_horizons": 12,
      "avg_r_squared": 0.131,
      "avg_irf": 0.711,
      "max_irf": 2.392,
      "horizon_max_response": "h_10"
    },
    "bvar_minnesota": {
      "n_vars": 2,
      "n_lags": 2,
      "n_obs": 243,
      "r_squared": -0.009,
      "model_quality": "weak",
      "irf_summary": {
        "max_response": 9.195,
        "horizon_max_response": 0,
        "persistence": 17.574
      }
    }
  }
}
```

## Notas

- Artefatos `.pkl` e `.json` são ignorados pelo git (`.gitignore`)
- Para produção, armazenar em object storage (S3, GCS, etc.)
- Manter registro de versões em `models_registry.json` (próximo passo)

