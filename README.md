# Análise preditiva de Influenza A no município de São Paulo utilizando IA com dados do SIVEP-Gripe

Protótipo acadêmico (TCC) de análise temporal e preditiva de casos de Influenza A
(SRAG) no município de São Paulo, a partir de dados públicos do SIVEP-Gripe/SINAN
(DATASUS). Não é ferramenta oficial de vigilância epidemiológica.

## Documentação

O documento consolidado do núcleo prático (ETL, banco, backend e modelo) com
matriz de rastreabilidade e referências é
[`docs/documentacao_projeto.md`](docs/documentacao_projeto.md).

| Documento | Conteúdo |
| --------- | -------- |
| [`docs/documentacao_projeto.md`](docs/documentacao_projeto.md) | Documentação técnica consolidada (ABNT), rastreabilidade e referências. |
| [`docs/requisitos.md`](docs/requisitos.md) | Requisitos funcionais (RF001 a RF004) e não funcionais. |
| [`docs/arquitetura_descricao.md`](docs/arquitetura_descricao.md) | Descrição da arquitetura. |
| [`docs/plano_nuvem.md`](docs/plano_nuvem.md) | Plano de nuvem (AWS): planejamento. |
| [`docs/plano_seguranca.md`](docs/plano_seguranca.md) | Plano de segurança (CORS, credenciais, LGPD). |
| [`docs/documentacao_backend.md`](docs/documentacao_backend.md) | Backend/API REST (FastAPI). |
| [`docs/documentacao_frontend.md`](docs/documentacao_frontend.md) | Frontend/dashboard (Next.js) e integração com a API. |
| [`docs/documentacao_modelo.md`](docs/documentacao_modelo.md) | Modelo preditivo (Random Forest). |
| [`docs/dicionario_banco.md`](docs/dicionario_banco.md) | Dicionário do banco de dados e DER. |
| [`docs/dicionario_dados.md`](docs/dicionario_dados.md) | Dicionário de dados e ficha de rastreabilidade. |
| [`docs/relatorio_qualidade_dados.md`](docs/relatorio_qualidade_dados.md) | Relatório de qualidade de dados (ISO/IEC 25012). |

## Estrutura do repositório

- `data/`: base bruta preservada e artefatos tratados.
- `scripts/`: ETL (`etl_coleta.py`, `etl_tratamento.py`) e treino (`train_model.py`).
- `database/`: `schema.sql`, `indexes.sql`, `seed.sql`.
- `backend/`: API REST FastAPI (camadas) e testes.
- `frontend/`: dashboard web (Next.js + TypeScript) que consome a API REST.
- `models/`: modelo versionado (`.joblib`).
- `notebooks/`: experimento do modelo.
- `docs/`: documentação técnica e acadêmica.

## Testes

```bash
cd backend && uv run pytest -q
```
