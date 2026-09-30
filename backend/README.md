# Backend - Nucleo pratico (ETL / Banco / API / Modelo)

Ambiente Python do TCC "Analise preditiva de Influenza A no municipio de Sao Paulo
utilizando IA com dados do SIVEP-Gripe". Gerenciado com [uv](https://docs.astral.sh/uv/)
e Python 3.11.

## Preparar o ambiente

```bash
cd backend
uv sync
```

## Rodar o ETL (a partir da raiz do repositorio)

Os scripts de ETL ficam em `/scripts` (raiz do repositorio), mas o ambiente Python
esta em `/backend`. Rode-os pelo ambiente uv apontando o diretorio:

```bash
uv --directory backend run python ../scripts/etl_coleta.py
uv --directory backend run python ../scripts/etl_tratamento.py
```

Os scripts resolvem os caminhos a partir da raiz do repositorio de forma robusta
(independem do diretorio de trabalho atual).

## API REST (FastAPI)

A API expoe os dados historicos, a serie temporal, previsoes e metricas do
modelo. Estrutura em camadas: `app/routes` (endpoints), `app/services` (regras
de negocio), `app/repositories` (acesso a dados via SQLAlchemy), `app/models`
(ORM espelhando o schema do banco), `app/schemas` (Pydantic) e `app/core`
(configuracao e logs).

### Configuracao (sem credenciais no codigo)

A string de conexao vem da variavel de ambiente `DATABASE_URL`. Copie o exemplo
da raiz do repositorio e ajuste:

```bash
cp .env.example .env   # a partir da raiz do repositorio
```

- PostgreSQL (producao): `DATABASE_URL=postgresql+psycopg2://USUARIO:SENHA@HOST:5432/influenza_sp`
- SQLite (dev/testes): `DATABASE_URL=sqlite:///./influenza_dev.db`

### Subir a API

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Documentacao interativa (Swagger/OpenAPI): `http://127.0.0.1:8000/docs`.

### Endpoints

| Metodo | Rota | Descricao |
| ------ | ---- | --------- |
| GET | `/api/status` | Healthcheck (banco e modelo). |
| GET | `/api/dados` | Serie filtrada por periodo (`ano_inicio`, `semana_inicio`, `ano_fim`, `semana_fim`). |
| GET | `/api/series-temporais` | Serie semanal municipal (opcional `apenas_treino`). |
| GET | `/api/previsoes` | Previsao de N semanas (padrao 6); usa modelo treinado ou baseline. |
| GET | `/api/metricas` | MAE/RMSE/MAPE/acerto direcional do modelo ativo. |
| GET | `/api/unidades-notificacao` | Unidades de notificacao (a fonte pode nao popular NM_UN_INTE). |

Todas as respostas seguem o envelope padronizado `{sucesso, dados, mensagem}`.

## Rodar os testes

```bash
cd backend
uv run pytest -q            # toda a suite (ETL + API)
uv run pytest tests/test_api.py -q
uv run pytest tests/test_etl.py -q
```

Os testes da API usam SQLite em memoria e o `TestClient` do FastAPI (sem
dependencia de servidor Postgres).
