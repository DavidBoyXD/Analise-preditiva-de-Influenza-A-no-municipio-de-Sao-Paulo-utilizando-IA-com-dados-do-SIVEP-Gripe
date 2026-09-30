# Descrição da Arquitetura

> Documento de arquitetura do TCC "Análise preditiva de Influenza A no município
> de São Paulo utilizando IA com dados do SIVEP-Gripe", conforme a seção 6.8 do
> Manual Interno (Arquitetura, nuvem e segurança) e o Anexo de Qualidade ISO/IEC
> v4 como referência normativa. Protótipo acadêmico. A camada de nuvem é
> **planejamento documentado**, não provisionado neste ambiente (ver
> [`docs/plano_nuvem.md`](plano_nuvem.md) e [`docs/plano_seguranca.md`](plano_seguranca.md)).

## 1. Visão geral

O sistema segue uma arquitetura em camadas, integrando frontend, backend, banco
relacional e modelo de aprendizado de máquina. O núcleo prático **efetivamente
construído** nesta entrega compreende: ETL, banco PostgreSQL, API REST em FastAPI
e o modelo Random Forest. O **frontend em Next.js** e a **implantação em nuvem
AWS** são a **fase seguinte**, aqui descritas como planejamento.

## 2. Componentes

| Componente | Tecnologia | Estado | Responsabilidade |
| ---------- | ---------- | ------ | ---------------- |
| Frontend / dashboard | **Next.js** (React) | Planejado (fase futura) | Consulta ao usuário: filtros por período e unidade de notificação, gráficos, cards e comparação real × previsto. |
| Backend / API REST | **FastAPI** (Python) | Construído (FEAT-003) | Expõe dados, séries, previsões, métricas e status em JSON padronizado. |
| Banco de dados | **PostgreSQL** (RDS em produção) | Construído (FEAT-002) | Armazena fontes, arquivos, séries, registros, modelo, métricas e logs (9 tabelas em 3FN). |
| Modelo preditivo | **Python** (scikit-learn Random Forest) | Construído (FEAT-004) | Modelo serializado (`.joblib`) carregado em memória pela API. |
| Armazenamento de objetos | **Amazon S3** | Planejado (fase futura) | Backup do arquivo bruto, dos artefatos tratados e do modelo versionado. |
| Computação | **Amazon EC2** | Planejado (fase futura) | Hospedagem do backend/API. |

## 3. Fluxo de dados

```
DATASUS/SIVEP-Gripe (CSV consolidado)
        │  (RF003 - ETL)
        ▼
[ scripts/etl_coleta.py -> etl_tratamento.py ]
        │  base_tratada.csv + serie_temporal_semanal.csv
        ▼
[ PostgreSQL / RDS ]  ← 9 tabelas 3FN (schema.sql / seed.sql / indexes.sql)
        │
        ├──────────────► [ scripts/train_model.py ]  (RF004)
        │                       │  modelo_rf_v1.joblib + métricas no banco
        │                       ▼
        │                 [ models/*.joblib ]
        ▼                       │  carregado em memória na inicialização
[ FastAPI / EC2 ] ◄────────────┘  (serviço de previsão)
   /api/status /api/dados /api/series-temporais
   /api/previsoes /api/metricas /api/unidades-notificacao
        │  JSON padronizado {sucesso, dados, mensagem}
        ▼
[ Frontend Next.js ]  (fase futura: dashboard)
        ▼
   Usuário comum
```

Diagrama de arquitetura de referência (pipe-filter) disponível em
`Documentos_Para_Desenv_TCC/TCC_CDHM_Diagrama_Arquitetura_PipeFilter.svg`.

## 4. Comunicação entre componentes

- **Frontend ↔ Backend:** HTTP/REST com JSON padronizado. CORS configurável por
  variável de ambiente (`CORS_ORIGENS`). Previsões são retornadas com marcação de
  origem (`modelo_treinado`/`baseline`) para permitir a separação visual entre
  dado real e estimativa (RF002; ISO/IEC 25059 — Alerta de perigo).
- **Backend ↔ Banco:** SQLAlchemy, string de conexão em `DATABASE_URL`. Código
  portável entre PostgreSQL (produção) e SQLite (testes/desenvolvimento).
- **Backend ↔ Modelo:** o serviço de previsão carrega o `.joblib` de `models/` na
  inicialização (padrão "modelo em memória" do TC2, seção 4.6.4) e expõe
  `prever_series(historico, horizonte)`.
- **ETL/Treino ↔ Banco:** os scripts escrevem a série e as métricas via SQLAlchemy;
  a origem de cada dado é registrada em `fonte_dados`/`arquivo_dados`/`log_processamento`
  (ISO/IEC 25012 — Rastreabilidade; ISO/IEC 27002 8.15/8.16).

## 5. Variáveis de ambiente

Definidas em `.env` (nunca versionado) e documentadas em `.env.example` na raiz:

| Variável | Descrição |
| -------- | --------- |
| `DATABASE_URL` | String de conexão SQLAlchemy (PostgreSQL em produção, SQLite em dev/teste). |
| `APP_NOME` / `APP_VERSAO` | Metadados exibidos na documentação OpenAPI. |
| `HORIZONTE_PREVISAO_SEMANAS` | Horizonte padrão de previsão (6). |
| `CAMINHO_MODELOS` | Diretório onde a API procura o `.joblib`. |
| `CO_MUN_RES_PADRAO` | Código IBGE do município de referência (355030). |
| `CORS_ORIGENS` | Origens permitidas para CORS. |

## 6. Decisões arquiteturais

| Decisão | Justificativa | Fonte |
| ------- | ------------- | ----- |
| Arquitetura em camadas (rotas/serviços/repositórios/modelos/schemas) | Modularidade e modificabilidade (trocar o modelo não reescreve a API). | Manual 6.4; ISO/IEC 25010 (Manutenibilidade) |
| Modelo carregado em memória na inicialização | Reduz latência da previsão; padrão do TC2 4.6.4. | TC2 4.6.4 |
| Camada de acesso portável (PostgreSQL/SQLite) | Testes rápidos sem servidor Postgres; troca por RDS sem reescrever a lógica. | ISO/IEC 25010 (Capacidade de substituição) |
| Tolerância a falhas do preditor (503 isolado) | Falha do modelo não deve derrubar dados históricos (RF001). | ISO/IEC 25010 (Tolerância a falhas) |
| Modelo isolado em camada de serviço própria | Permite substituir o modelo sem impacto na API. | ISO/IEC 27002 8.32 (gestão de mudanças) |

## 7. Limites do ambiente atual

- Não há servidor PostgreSQL nem AWS provisionados neste ambiente. O banco é
  validado via container Docker (PostgreSQL 16) e via SQLite nos testes; a nuvem é
  descrita como planejamento em [`docs/plano_nuvem.md`](plano_nuvem.md).
- O frontend Next.js ainda não foi implementado; os endpoints já entregam o
  contrato JSON que o dashboard consumirá.

## 8. Referências

Ver a seção de referências ABNT (NBR 6023) em
[`docs/documentacao_projeto.md`](documentacao_projeto.md), seção 8.
