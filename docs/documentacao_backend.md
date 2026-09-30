# Documentacao do Backend (API REST FastAPI)

> Modulo **backend** do nucleo pratico do TCC "Analise preditiva de Influenza A
> no municipio de Sao Paulo utilizando IA com dados do SIVEP-Gripe". Sustenta os
> requisitos **RF001** (previsao), **RF002** (consulta de dados historicos com
> tolerancia a falhas) e **RF003** (persistencia/rastreabilidade). Prototipo
> academico - nao e ferramenta oficial de vigilancia.

## 1. Visao geral

A API foi construida em **FastAPI** com arquitetura **em camadas**, conforme o
padrao de arquitetura definido no Manual Interno (secao 6.5) e no anexo de
qualidade. O acesso a dados usa **SQLAlchemy**, com string de conexao lida da
variavel de ambiente `DATABASE_URL`. O codigo e compativel tanto com
**PostgreSQL** (producao, banco entregue em FEAT-002) quanto com **SQLite**
(testes e desenvolvimento local), sem SQL cru dependente de dialeto.

## 2. Estrutura em camadas

| Camada | Diretorio | Responsabilidade |
| ------ | --------- | ---------------- |
| Rotas | `backend/app/routes` | Endpoints REST, validacao de query e envelope de resposta. |
| Servicos | `backend/app/services` | Regras de negocio (montagem da serie, previsao, metricas). |
| Repositorios | `backend/app/repositories` | Consultas SQLAlchemy (serie, modelo/metricas, unidades). |
| Modelos ORM | `backend/app/models` | Mapeamento das 9 tabelas do schema (FEAT-002). |
| Schemas | `backend/app/schemas` | Modelos Pydantic de request/response + envelope padrao. |
| Nucleo | `backend/app/core` | Configuracao (pydantic-settings) e logs estruturados. |
| Ponto de entrada | `backend/app/main.py` | App FastAPI, CORS, middleware de logs, handlers globais, Swagger. |

## 3. Endpoints REST

Todos retornam o envelope padronizado `{sucesso, dados, mensagem}`.

| Metodo | Rota | Requisito | Descricao |
| ------ | ---- | --------- | --------- |
| GET | `/api/status` | - | Healthcheck: verifica banco (`SELECT 1`) e modelo carregado. |
| GET | `/api/dados` | RF002 | Serie por periodo (`ano_inicio`, `semana_inicio`, `ano_fim`, `semana_fim`), com validacao de intervalo. |
| GET | `/api/series-temporais` | RF002 | Serie semanal municipal (opcional `apenas_treino`). |
| GET | `/api/previsoes` | RF001 | Previsao de N semanas (padrao 6); modelo treinado ou baseline. |
| GET | `/api/metricas` | RF001 | MAE/RMSE/MAPE/acerto direcional do modelo ativo (lidos do banco). |
| GET | `/api/unidades-notificacao` | RF003 | Unidades de notificacao (documenta a pendencia de NM_UN_INTE). |

Documentacao interativa **OpenAPI/Swagger** em `/docs`.

## 4. Envelope, validacao e tratamento de erros

- **Envelope**: `RespostaPadrao` (`app/schemas/common.py`) -> `{sucesso, dados, mensagem}`.
- **Validacao de entrada**: intervalo `inicio <= fim` validado em
  `dados_service`; parametros fora de dominio (semana 1-53) validados na rota.
  Erros retornam **400** (regra de negocio) ou **422** (parametro invalido), com
  mensagem clara em Portugues-Brasil e **sem vazar stack trace**.
- **Handlers globais** (`app/main.py`): `ErroValidacao` (400),
  `RequestValidationError` (422), `RecursoNaoEncontrado` (404),
  `PrevisaoIndisponivel` (503) e `Exception` (500). Todos usam o envelope.
- **Logs estruturados** (`app/core/logging_config.py`): timestamp, nivel,
  origem e mensagem; o middleware registra metodo, rota, status e duracao.

## 5. Tolerancia a falhas do modulo preditivo (RF002)

O servico de previsao (`app/services/previsao_service.py`):

1. carrega um modelo `.joblib` do diretorio `models/` na inicializacao (padrao
   "modelo carregado em memoria" descrito no TC2, secao 4.6.4);
2. se nao houver modelo, usa um **baseline sazonal-ingenuo** calculado a partir
   da serie de treino lida do banco (sem dado fixo mockado em producao);
3. encapsula qualquer falha em `PrevisaoIndisponivel` -> **503**, de modo que a
   indisponibilidade do modelo **nao derruba** os endpoints de dados historicos.

O modelo real (Random Forest) e treinado e integrado em **FEAT-004**; aqui fica
pronta a interface (`prever_series`) que ele deve expor.

## 6. Seguranca de configuracao

- Nenhuma credencial no codigo. `DATABASE_URL` vem de variavel de ambiente.
- `.env.example` (raiz do repositorio) documenta as variaveis sem segredos.
- `.env` esta no `.gitignore`.

## 7. Testes

`backend/tests` (pytest + `TestClient` + SQLite em memoria). `conftest.py`
popula um banco de teste com serie, modelo ativo, metricas e unidade. Cobrem:
status, dados (periodo valido/invalido/fora de dominio), series-temporais,
metricas, previsoes (baseline), unidades, formato do envelope, recurso vazio e
casos 404/503.

```bash
cd backend && uv run pytest -q
```

## 8. Rastreabilidade de referencias

Cada decisao de projeto do backend foi ancorada nos documentos-fonte do TCC e em
normas/documentacoes tecnicas publicas.

| Conteudo aplicado no backend | Fonte utilizada | Localizacao / link |
| ---------------------------- | --------------- | ------------------ |
| Requisitos RF001/RF002/RF003; endpoints de dados, serie, previsao, metricas e status | TCC - C D H M (TC2), secoes de requisitos funcionais | `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx` |
| Arquitetura em camadas; retorno JSON padronizado; validacao de entrada; tratamento de erros; logs; Swagger; nao expor credenciais | Manual Interno de Desenvolvimento (secoes 6.5-6.6) | `Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx` |
| Modelo carregado em memoria na inicializacao (servico de previsao) | TCC - C D H M (TC2), secao 4.6.4 | `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx` |
| Tolerancia a falhas (previsao indisponivel nao derruba dados historicos); confiabilidade | Anexo de Qualidade ISO/IEC 25000 v4 (ISO/IEC 25010 - Confiabilidade/Tolerancia a falhas) | `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx` |
| Seguranca de configuracao (segregacao de segredos, `.env.example`) | Anexo de Qualidade (ISO/IEC 27002) e Manual Interno | `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx` |
| Nomes de tabelas/colunas do ORM; pendencia de NM_UN_INTE; escopo municipal | Dicionario de banco (FEAT-002) e schema | [`docs/dicionario_banco.md`](dicionario_banco.md), `database/schema.sql` |
| Serie temporal semanal, casos-proxy e exclusao das 8 semanas recentes | Relatorio de qualidade de dados (FEAT-001) | [`docs/relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md) |
| FastAPI (rotas, dependencias, OpenAPI, TestClient) | Documentacao oficial do FastAPI | https://fastapi.tiangolo.com/ |
| SQLAlchemy 2.0 (engine, ORM declarativo, sessao) | Documentacao oficial do SQLAlchemy | https://docs.sqlalchemy.org/en/20/ |
| pydantic-settings (leitura de configuracao por variavel de ambiente) | Documentacao oficial do Pydantic | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| Semana epidemiologica (conceito) | Ministerio da Saude / SIVEP-Gripe (DATASUS) | https://opendatasus.saude.gov.br/ |

> Uso de IA no desenvolvimento seguindo as normas do CNPq (documento
> `Documentos_Para_Desenv_TCC/Normas CNPQ Uso de IA.pdf`).
