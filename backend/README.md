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

## Rodar os testes

```bash
cd backend
uv run pytest tests/test_etl.py -q
```
