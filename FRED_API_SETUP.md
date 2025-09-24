# 🔑 Configuração da FRED API Key

## **Passo 1: Obter FRED API Key (Gratuita)**

1. **Acesse**: https://fred.stlouisfed.org/docs/api/api_key.html
2. **Clique em**: "Request API Key"
3. **Preencha o formulário**:
   - Nome: Seu nome
   - Email: Seu email
   - Organização: Sua empresa/universidade
   - Uso: "Research/Educational"
4. **Clique em**: "Submit"
5. **Copie sua API Key** (será enviada por email)

## **Passo 2: Configurar no Sistema**

### **Opção A: Variável de Ambiente (Recomendado)**
```bash
# macOS/Linux
export FRED_API_KEY="sua_api_key_aqui"

# Windows
set FRED_API_KEY=sua_api_key_aqui
```

### **Opção B: Arquivo de Configuração**
Edite o arquivo `config.env`:
```bash
FRED_API_KEY=sua_api_key_aqui
```

### **Opção C: Diretamente no Código (Temporário)**
Edite `app/core/config.py`:
```python
FRED_API_KEY: Optional[str] = "sua_api_key_aqui"
```

## **Passo 3: Testar Configuração**

```bash
# Testar se a variável está configurada
echo $FRED_API_KEY

# Reiniciar o servidor
python run.py
```

## **Passo 4: Verificar Logs**

Após configurar, você deve ver nos logs:
```
✅ [FRED] Sucesso ao buscar CLI OECD (X registros)
```

Em vez de:
```
⚠️ FRED_API_KEY não configurada - usando modo limitado
```

## **🔧 Solução Rápida**

Se você quiser testar imediatamente sem API key, o sistema já funciona com dados simulados, mas para dados reais da FRED, você precisa da API key.

## **📊 Benefícios da FRED API**

- ✅ **Gratuita** (sem limites para uso educacional)
- ✅ **Estável** (99.9% uptime)
- ✅ **Dados OECD CLI** disponíveis
- ✅ **Rate limiting generoso**
- ✅ **Dados históricos completos**

## **🚨 Problemas Comuns**

### **Erro 400 Bad Request**
- Verifique se a API key está correta
- Certifique-se de que não há espaços extras

### **Erro 403 Forbidden**
- API key inválida ou expirada
- Solicite uma nova API key

### **Rate Limit Exceeded**
- Aguarde alguns minutos
- FRED tem limites generosos, raramente acontece
