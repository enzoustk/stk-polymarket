# Striker Polymarket API

**Striker Polymarket API** é uma ferramenta robusta e de alta performance para extração e análise de dados da [Polymarket](https://polymarket.com/). 

Projetada para *traders* e analistas, a biblioteca combina dados da API REST oficial (Gamma/Data API) com o Subgraph (Goldsky/The Graph) para reconstruir históricos de negociação, calcular PnL (Profit and Loss) e analisar o CLV (Closing Line Value) das operações.

## 🚀 Funcionalidades Principais

* **Híbrido REST + GraphQL:** Utiliza o Subgraph para descobrir posições de forma rápida e a API REST para obter detalhes granulares de mercado.
* **Processamento Paralelo:** Arquitetura *multi-threaded* com `concurrent.futures` para baixar milhares de trades e preços históricos simultaneamente.
* **Gestão Inteligente de Rate Limit:** Sistema integrado de *backoff* exponencial e *jitter* para lidar com erros 429 e evitar bloqueios de IP.
* **Cálculo de CLV (Client Lifetime Value):** Analisa a performance do trader comparando o preço médio de entrada contra o preço de fechamento/início do evento.
* **Histórico de Preços (CLOB):** Ferramentas para buscar o preço exato de um ativo em momentos específicos (ex: no apito inicial de um jogo).
* **Animações de CLI:** Feedback visual de progresso para operações longas.

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone [https://github.com/enzoustk/striker_polymarket_api.git](https://github.com/enzoustk/striker_polymarket_api.git)
   cd striker_polymarket_api
    ````

2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Como Usar

### 1\. Buscar PnL e Posições (Ativas e Fechadas)

O módulo `subgraph` orquestra a busca completa, cruzando dados de saldo com metadados de mercado.

```python
from stk_polymarket.api.subgraph import fetch_pnl_data

USER_ADDRESS = "0xSeuEnderecoPolymarket..."

# Retorna dois DataFrames: Posições Fechadas e Posições Ativas
df_closed, df_active = fetch_pnl_data(user_address=USER_ADDRESS)

print(f"Total de posições fechadas: {len(df_closed)}")
print(df_closed.head())
```

### 2\. Análise de CLV (Customer Lifetime Value)

Calcula a eficiência dos seus trades comparando o preço pago vs. preço real no início do evento.

```python
from stk_polymarket.api.rest import calculate_clv

# Supondo que você já tenha um DataFrame 'df_positions' com as colunas necessárias
# (conditionId, asset, start_time, match_start_price, etc.)

df_resultado = calculate_clv(
    user_address=USER_ADDRESS,
    df=df_positions
)

print(df_resultado[['asset', 'price_clv', 'odds_clv']])
```

### 3\. Histórico de Preços

Busca o preço de um ativo no momento exato em que um evento começou (útil para *backtesting*).

```python
from stk_polymarket.api.modules.rest_api.price_history import get_match_start_price
from datetime import datetime
import pytz

market_id = "TOKEN_ID_DO_MERCADO"
match_date = datetime(2023, 10, 25, 15, 0, 0, tzinfo=pytz.UTC)

price = get_match_start_price(
    market_id=market_id, 
    match_datetime=match_date,
    hours_before=1 # Busca dados de até 1h antes do início
)

print(f"Preço no início do jogo: {price}")
```

### 4\. Trading — Envio de Ordens (CLOB V2, baixa latência)

> ⚠️ A Polymarket **descontinuou** o `py-clob-client` (V1) e migrou para a **CLOB V2**
> (sem retrocompatibilidade). Esta lib usa o sucessor oficial `py-clob-client-v2`.
> Instale o extra `fast` (`pip install -e .[fast]`) para o backend `coincurve`
> (assinatura ECDSA sub-ms).

O `FastTrader` é o caminho de **baixa latência**: pré-aquece credenciais, metadados
(tick_size/neg_risk) e a conexão TLS/HTTP2, e no envio faz só *build → sign → 1 POST*
(zero round-trips extras). Carteira **EOA** por padrão (`signature_type=0`).

```python
from stk_polymarket import FastTrader, OrderType

TOKEN_ID = "7132104567...."

# Pré-aquece tudo uma vez (deriva creds, cacheia tick/neg, abre a conexão)
ft = FastTrader(private_key="0x...").warmup(token_ids=[TOKEN_ID])

# Marketable (FOK / FAK)
ft.fok(TOKEN_ID, price=0.62, size=10, side="BUY")

# Limit GTC, e pré-assinatura para disparo ainda mais rápido
ft.gtc(TOKEN_ID, price=0.55, size=20, side="BUY")
signed = ft.presign(TOKEN_ID, 0.50, 20, "BUY")   # assina agora...
ft.send(signed, OrderType.GTC)                    # ...dispara depois (só HMAC + POST)
```

Para o caminho simples via SDK (latência não crítica) use
`stk_polymarket.trading.send.send_order`. Para reutilizar credenciais já derivadas,
gere-as uma vez com `stk_polymarket.connection.auth.auth(private_key)` e passe via
`FastTrader(private_key, creds=...)`.

> **Latência:** o gargalo é a rede, não a CPU (assinatura ~sub-ms com `coincurve`). O
> maior ganho é **pré-aquecer a conexão** (remove o handshake TLS de ~centenas de ms do
> caminho da ordem) e **colocation** próximo ao edge da Cloudflare.

## 🛠️ Estrutura do Projeto

  * **`config.py`**: Centraliza os Endpoints (Goldsky, Gamma API, CLOB, Activity).
  * **`subgraph.py`**: Ponto de entrada para buscar posições via GraphQL.
  * **`rest_api/`**:
      * `clv.py`: Lógica complexa para baixar trades e calcular métricas de valor.
      * `price_history.py`: Busca histórica na API CLOB (Order Book).
      * `fetch.py`: Wrappers para chamadas REST com paginação e retry.
  * **`helpers.py`**: Utilitários visuais (loading bars) e funções matemáticas seguras.

## ⚠️ Notas sobre Rate Limits

Esta biblioteca foi configurada para ser agressiva na coleta de dados, mas respeitosa com os limites da API. Se você encontrar muitos erros de *timeout* ou *rate limit*, verifique a variável `max_workers` nas chamadas de função ou aumente os tempos de `sleep` no módulo `fetch.py`.

## 📝 Autores

  * **enzoustk**
