# Documentação do Projeto — Núcleo Prático

> Documentação técnica consolidada do TCC "Análise preditiva de Influenza A no
> município de São Paulo utilizando inteligência artificial com dados do
> SIVEP-Gripe (subsistema DATASUS)". Reúne, em um único documento, tudo o que foi
> efetivamente construído no núcleo prático (ETL, banco de dados, backend/API e
> modelo preditivo), amarra os atributos de qualidade às normas ISO/IEC e traz a
> rastreabilidade de cada decisão à sua fonte.
>
> **Posicionamento (regra do Manual, seção 2):** este sistema é um **protótipo
> acadêmico** de apoio à visualização, análise exploratória e previsão de dados
> epidemiológicos. **Não** é ferramenta oficial de vigilância, **não** substitui
> plataformas governamentais e **não** comprova melhoria direta em decisões de
> saúde pública.

Instituição: Universidade Paulista — UNIP · Curso: Ciência da Computação ·
São Paulo, 2026.

---

## Sumário

1. Apresentação e escopo
2. Coleta e tratamento de dados (ETL)
3. Banco de dados
4. Backend / API REST
5. Modelo preditivo
6. Qualidade e segurança (ISO/IEC 25010/25012/25059/27002)
7. Limitações e trabalhos futuros
8. Referências (ABNT NBR 6023)

Anexos ao documento: matriz de rastreabilidade (seção 6.6) e mapeamento de KPIs
(seção 6.5). Documentos complementares:
[`requisitos.md`](requisitos.md),
[`arquitetura_descricao.md`](arquitetura_descricao.md),
[`plano_nuvem.md`](plano_nuvem.md),
[`plano_seguranca.md`](plano_seguranca.md),
[`documentacao_backend.md`](documentacao_backend.md),
[`documentacao_modelo.md`](documentacao_modelo.md),
[`dicionario_banco.md`](dicionario_banco.md),
[`dicionario_dados.md`](dicionario_dados.md),
[`relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md),
[`metricas_modelos.md`](metricas_modelos.md).

---

## 1. Apresentação e escopo

### 1.1 Objetivo do sistema

Desenvolver um protótipo web para análise temporal e preditiva de casos de
Influenza A (SRAG) no **município de São Paulo**, a partir de dados públicos do
SIVEP-Gripe/SINAN (DATASUS): coletar, tratar, armazenar, analisar e disponibilizar
dados históricos e estimativas futuras via API REST, com dashboard previsto para a
fase seguinte.

### 1.2 Delimitações obrigatórias

Registradas conforme a seção 3 do Manual Interno:

| Delimitação | Definição |
| ----------- | --------- |
| **Recorte geográfico** | Município de São Paulo (CO_MUN_RES = 355030). |
| **Período dos dados** | 2009–2019 (SINAN harmonizado) e 2022 em diante (SIVEP-Gripe), com **hiato deliberado em 2020–2021** (ausente na fonte, não preenchido com zeros artificiais). |
| **Granularidade** | Série temporal **semanal** (semana epidemiológica). |
| **Variável-alvo** | Contagem semanal de casos-proxy de Influenza A no município de São Paulo (ver proxy PCR_FLUASU, seção 2.3). |
| **Horizonte preditivo** | 6 semanas subsequentes. |
| **Baseline** | Modelo simples de referência (sazonal-ingênuo). |
| **Critério de sucesso** | Registrar MAE, RMSE, MAPE e acerto direcional; comparar com baseline, SARIMA e Prophet sob walk-forward; aplicar teste de significância (Diebold-Mariano/Wilcoxon); apresentar gráfico real × previsto. Resultado mensurável, não narrativo. |
| **Granularidade de consulta** | Por unidade de notificação (`NM_UN_INTE`), **não** por bairro/região. A modelagem é sempre **municipal**. |

### 1.3 Escopo desta entrega

Construídos: **ETL** (RF003), **banco de dados** (RF003), **backend/API** (RF001,
RF002, RF003) e **modelo preditivo** (RF004). O **frontend Next.js** e a
**implantação em nuvem AWS** são **fase seguinte** (documentados como planejamento
em [`arquitetura_descricao.md`](arquitetura_descricao.md),
[`plano_nuvem.md`](plano_nuvem.md) e [`plano_seguranca.md`](plano_seguranca.md)).

---

## 2. Coleta e tratamento de dados (ETL)

Detalhamento completo em [`dicionario_dados.md`](dicionario_dados.md) e
[`relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md). Resumo:

### 2.1 Fonte e rastreabilidade

- Fonte: SIVEP-Gripe / SINAN (DATASUS), dados públicos de SRAG.
- Arquivo original: `Documentos_Para_Desenv_TCC/Dados consolidados e padronizados
  2009 a 2019 e 2022 a 2026.csv` (48.775 registros, encoding UTF-8 com BOM,
  separador `;`).
- Base bruta preservada (cópia fiel, nunca sobrescrita) em
  `data/raw/sivep_gripe_consolidado_2009_2026.csv`.
- Scripts: `scripts/etl_coleta.py` (leitura/metadados) e
  `scripts/etl_tratamento.py` (filtro, derivações, proxy, série).

### 2.2 Processamento e resultados

- Filtro do município de São Paulo (355030): **13.139** de 48.775 registros.
- Derivação de `ANO` e `SEMANA_EPI` a partir de `DT_SIN_PRI`/`SEM_PRI`.
- Série temporal semanal contínua: **832 semanas** (semanas sem casos = 0; os anos
  ausentes 2020–2021 **não** são preenchidos com zeros artificiais).
- As **8 semanas epidemiológicas mais recentes** são marcadas como reservadas
  (`RESERVADA_ATRASO_NOTIFICACAO = True`, `USAR_NO_TREINO = False`) por atraso de
  notificação.
- Artefatos: `data/processed/base_tratada.csv` e
  `data/processed/serie_temporal_semanal.csv`.

### 2.3 Limitação crítica — proxy PCR_FLUASU

Os campos de confirmação laboratorial da Tabela 1 do TC2 (`CLASSI_FIN`,
`PCR_RESUL`, `POS_PCRFLU`, `TP_FLU_PCR`, `POS_AN_FLU`, `TP_FLU_AN`) **não existem**
no arquivo consolidado. Adota-se a **regra de proxy**: registro com `PCR_FLUASU`
preenchido (não vazio) conta como caso-proxy de Influenza A. Os campos ausentes
**não foram fabricados**. Distribuição real em SP: vazio=5.732, `1`=3.505,
`3`=2.073, `4`=790, `2`=736, `5`=160, `6`=143 (total proxy = 7.407). Amarração
ISO/IEC 25012: Exatidão e Consistência (ver seção 6.2).

### 2.4 Descompasso de granularidade — NM_UN_INTE ausente

O TC2 previa `NM_UN_INTE` (unidade de notificação) como granularidade de consulta;
o campo **não existe** no CSV. A modelagem é sempre municipal e **não** foram
criadas estruturas de bairro/região. A tabela `unidade_notificacao` existe como
estrutura, com o campo registrado como pendência (ISO/IEC 25012 — Completude).

---

## 3. Banco de dados

Detalhamento completo em [`dicionario_banco.md`](dicionario_banco.md); DER em
`docs/der_banco.mmd`/`docs/der_banco.png`; scripts em `database/`.

### 3.1 Modelo relacional (3FN)

Banco PostgreSQL em Terceira Forma Normal, com **9 tabelas**, nomenclatura do
Manual de Documentação de Bancos (PK `id_<entidade>`, FK
`id_<entidade_referenciada>`, índices `ix_...`, únicos `uq_...`, checks `ck_...`):

| Tabela | Função |
| ------ | ------ |
| `fonte_dados` | Fonte externa (DATASUS/SIVEP-Gripe). |
| `arquivo_dados` | Arquivo bruto/tratado, período e ficha de rastreabilidade. |
| `unidade_notificacao` | Unidade de notificação (`nm_un_inte`); **não populada** pela fonte atual (pendência). |
| `semana_epidemiologica` | Ano, número da semana, datas inicial/final. |
| `registro_epidemiologico` | Dados agregados por semana (casos-proxy). |
| `serie_temporal` | Série semanal consolidada, com flags de reserva das 8 semanas. |
| `modelo_preditivo` | Nome, versão, algoritmo, caminho do `.joblib`, versão ativa. |
| `metrica_modelo` | MAE, RMSE, MAPE, acerto direcional, teste de significância. |
| `log_processamento` | Timestamp, origem, mensagem, stack trace. |

### 3.2 Artefatos e validação

- `database/schema.sql` (DDL com PK/FK/CHECK/UNIQUE, datas em `DATE`/`TIMESTAMP`,
  `COMMENT ON` em todas as tabelas e colunas), `database/indexes.sql` (12 índices
  justificados) e `database/seed.sql`.
- Validado em **PostgreSQL 16 via container Docker** (0 FKs órfãs; sem tabelas
  bairro/região; 0 tabelas/colunas sem comentário) e compatível com **SQLite**
  para os testes do backend.
- Removidas as tabelas `bairro`, `regiao` e `bairro_predicao` (a fonte é
  municipal, sem granularidade de bairro).

---

## 4. Backend / API REST

Detalhamento completo em [`documentacao_backend.md`](documentacao_backend.md).
Resumo:

### 4.1 Arquitetura em camadas

FastAPI com camadas **rotas / serviços / repositórios / modelos ORM / schemas** e
núcleo de configuração/logs. Acesso a dados via SQLAlchemy, `DATABASE_URL` por
variável de ambiente, portável entre PostgreSQL e SQLite.

### 4.2 Endpoints (contrato JSON `{sucesso, dados, mensagem}`)

| Método | Rota | Requisito | Descrição |
| ------ | ---- | --------- | --------- |
| GET | `/api/status` | — | Healthcheck (banco + modelo). |
| GET | `/api/dados` | RF001 | Série por período (valida intervalo). |
| GET | `/api/series-temporais` | RF001 | Série semanal municipal. |
| GET | `/api/previsoes` | RF002 | Previsão de 6 semanas (modelo ou baseline). |
| GET | `/api/metricas` | RF004 | MAE/RMSE/MAPE/acerto direcional do modelo ativo. |
| GET | `/api/unidades-notificacao` | RF003 | Unidades (documenta pendência de NM_UN_INTE). |

Documentação interativa OpenAPI/Swagger em `/docs`.

### 4.3 Validação, erros, logs e tolerância a falhas

- Validação de intervalo (`início <= fim`, semana 1–53) com **400/422** e mensagem
  clara, **sem vazar stack trace**.
- Handlers globais para `ErroValidacao` (400), validação (422),
  `RecursoNaoEncontrado` (404), `PrevisaoIndisponivel` (503) e `Exception` (500).
- Logs estruturados (timestamp, nível, origem) e middleware de requisição.
- **Tolerância a falhas:** a indisponibilidade do modelo retorna 503 **sem
  derrubar** os endpoints de dados históricos (RF001; ISO/IEC 25010).

### 4.4 Segurança de configuração

Nenhuma credencial no código; `.env.example` sem segredos; `.env` no `.gitignore`.
Detalhes em [`plano_seguranca.md`](plano_seguranca.md).

---

## 5. Modelo preditivo

Detalhamento completo em [`documentacao_modelo.md`](documentacao_modelo.md) e
[`metricas_modelos.md`](metricas_modelos.md); experimento em
`notebooks/experimentos_modelos.ipynb`. Resumo:

- **Modelo principal:** Random Forest (scikit-learn) com engenharia de atributos
  temporais (lags 1–4, médias móveis 3 e 5, sazonalidade seno/cosseno do ciclo de
  52 semanas + mês). Previsão recursiva de horizonte 6.
- **Protocolo:** walk-forward de origem expansiva (nunca aleatório).
- **Comparadores:** baseline sazonal-ingênuo, SARIMA (statsmodels), Prophet.
- **Métricas:** MAE, RMSE, MAPE (restrito a semanas com real > 0) + sMAPE + acerto
  direcional.
- **Significância:** Diebold-Mariano (com correção Harvey-Leybourne-Newbold, 1997)
  e Wilcoxon.
- **Versionamento:** `models/modelo_rf_v1.joblib`; métricas registradas em
  `modelo_preditivo`/`metrica_modelo` e servidas por `/api/metricas`.

### 5.1 Resultados observados (honestidade metodológica)

Valores efetivamente obtidos (walk-forward, horizonte 6):

| modelo | MAE | RMSE | sMAPE (%) | acerto direcional |
| ------ | --- | ---- | --------- | ----------------- |
| baseline (sazonal-ingênuo) | 8,28 | 22,86 | 47,33 | 0,512 |
| **random_forest** | 8,56 | 25,48 | 37,51 | 0,531 |
| sarima | 7,51 | 23,34 | 44,53 | 0,482 |
| prophet | 10,38 | 23,07 | 46,96 | 0,532 |

Diebold-Mariano do Random Forest frente a cada comparador: baseline p=0,512;
SARIMA p=0,336; Prophet p=0,542 — **nenhuma** diferença estatisticamente
significativa.

**Leitura honesta:** nesta série curta e esparsa, o Random Forest **não superou**
o baseline em MAE/RMSE, e o Diebold-Mariano **não indicou vantagem significativa**
frente a nenhum comparador; o SARIMA obteve o menor MAE. Conforme o Manual, o
modelo **não pode ser apresentado como comprovadamente superior**: o artefato é
entregue e integrado por completude do RF004, com desempenho reportado com
transparência.

---

## 6. Qualidade e segurança (ISO/IEC 25010/25012/25059/27002)

Os atributos de qualidade seguem o Anexo de Qualidade ISO/IEC 25000 v4
(`Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`), que
aplica quatro normas a dimensões distintas do sistema: **25010** (produto de
software), **25012** (dados), **25059** (sistemas de IA) e **27002** (controles de
segurança da informação).

### 6.1 ISO/IEC 25010:2023 — Qualidade do produto de software

| Característica | Aplicação no núcleo prático | Como validar |
| ------------- | --------------------------- | ------------ |
| Adequação funcional | RF001–RF004 cobrem os objetivos; endpoints retornam os dados filtrados. | Matriz de rastreabilidade (6.6); Pytest |
| Eficiência de desempenho | Tempo de resposta dos endpoints; carga do modelo em memória. | Medição de tempo; meta ≤ 2 s em teste |
| Compatibilidade | JSON padronizado e reaproveitável. | Validação de contrato/schema |
| Capacidade de interação | Mensagens de erro claras (dashboard futuro cobre o restante). | Revisão de mensagens/UX (futuro) |
| Confiabilidade (tolerância a falhas) | Falha do preditor não interrompe RF001 (503 isolado). | Teste de cenário de falha |
| Segurança | Credenciais fora do código; acesso administrativo planejado. | Revisão do `.env.example`; 27002 |
| Manutenibilidade | Camadas separadas; modelo isolado; logs analisáveis. | Revisão de arquitetura/código |
| Flexibilidade | Camada de acesso portável (PostgreSQL/SQLite); escalabilidade planejada. | Testes SQLite; DDL no PostgreSQL |
| Segurança operacional (Safety) | Previsão marcada como estimativa; nenhuma ação automática de saúde pública. | Origem da previsão; revisão de escopo |

### 6.2 ISO/IEC 25012:2008 — Qualidade dos dados

| Característica | Aplicação no pipeline | Referência |
| ------------- | --------------------- | ---------- |
| Exatidão | Proxy PCR_FLUASU aproxima o conceito de confirmação; não verificável na fonte. | `relatorio_qualidade_dados.md` §2 |
| Completude | Subnotificação, casos em andamento e ausência de NM_UN_INTE. | §3, §4 |
| Consistência | Codificação antiga de subtipo atravessa toda a série. | §2, §6 |
| Atualidade | Semanas recentes ainda "em maturação" → reserva das 8 semanas. | §5 |
| Rastreabilidade | `fonte_dados`/`arquivo_dados`/`log_processamento` documentam a origem. | `dicionario_banco.md` |
| Confidencialidade | Dados agregados; ressalva sobre NM_UN_INTE. | `plano_seguranca.md` §9 |

### 6.3 ISO/IEC 25059:2023 — Extensão para sistemas de IA

| Subcaracterística | Aplicação | Situação |
| ----------------- | --------- | -------- |
| Adaptabilidade funcional | Concept drift (mudança do padrão sazonal); retreinamento periódico. | Pendência declarada |
| Correção funcional (com ressalva) | MAE/RMSE/MAPE lidos como magnitude de erro, não critério binário. | Declarado na seção 5 |
| Robustez | Séries de consulta dominadas por zeros — cuidado de comunicação ao usuário. | Tratado no ETL/modelo |
| Transparência | Explicabilidade mínima (importância de variáveis do Random Forest). | Prevista no dashboard futuro |
| Controlabilidade | Sistema é somente leitura para previsões. | Declarado como limitação de escopo |

### 6.4 ISO/IEC 27002:2022 — Controles de segurança

Aplicados como boas práticas (não conformidade formal). Detalhes em
[`plano_seguranca.md`](plano_seguranca.md):

| Controle | Aplicação | Status |
| -------- | --------- | ------ |
| 5.15 / 8.2 / 8.3 | Controle e restrição de acesso administrativo. | Planejado |
| 8.5 | Autenticação segura (ex.: JWT) para rotas administrativas. | Planejado |
| 8.8 | Gestão de vulnerabilidades de dependências. | Planejado |
| 8.13 | Backup do RDS/S3 e teste de restore. | Planejado/parcial |
| 8.15 / 8.16 | Registro de eventos e monitoramento (`log_processamento` já ativo). | Parcial |
| 8.24 | Criptografia em trânsito/repouso; proteção de credenciais (`.env`). | Parcial |
| 8.32 | Gestão de mudanças (versão do modelo + registro ativo). | Implementado |

### 6.5 KPIs (Manual, seção 9.2)

| Módulo | KPI | Situação nesta entrega |
| ------ | --- | ---------------------- |
| Dados | Base tratada sem duplicidades introduzidas; campos essenciais analisados; série gerada. | Atendido (13.139 registros; 832 semanas). |
| API | Endpoints com JSON padronizado; tratamento de erro; resposta ≤ 2 s em teste. | Atendido (contrato + erros; meta de tempo). |
| Modelo | Comparação com baseline; MAE/RMSE/MAPE; gráfico real × previsto; métricas no banco. | Atendido (baseline+SARIMA+Prophet; DM/Wilcoxon). |
| Nuvem | API em EC2; banco em RDS; arquivos em S3; segredos fora do código. | Planejado (segredos já fora do código). |
| Dashboard | Filtros por período/unidade; gráficos dinâmicos; responsividade. | Fase futura (contrato de API pronto). |

---

### 6.6 Matriz de rastreabilidade (RF/objetivo → entregável → validação)

| RF / Objetivo | Entregável / Arquivo | Como validar (evidência) | KPI (9.2) |
| ------------- | -------------------- | ------------------------ | --------- |
| **RF003** — coletar/processar dados | `scripts/etl_coleta.py`, `scripts/etl_tratamento.py`, `data/processed/base_tratada.csv`, `serie_temporal_semanal.csv` | 13.139 registros de SP; série contínua; 8 semanas reservadas; `backend/tests/test_etl.py` (5 testes) | Dados |
| **RF003** — armazenar em banco relacional | `database/schema.sql`, `indexes.sql`, `seed.sql`, `docs/dicionario_banco.md`, `docs/der_banco.png` | Aplicação em PostgreSQL 16 (Docker): 0 FKs órfãs, 0 comentários faltando; compatível com SQLite | Dados |
| **RF001** — visualizar/consultar dados | `GET /api/dados`, `GET /api/series-temporais`, `docs/documentacao_backend.md` | `backend/tests/test_api.py`: filtro válido/ inválido, envelope JSON | API / Dashboard |
| **RF002** — exibir previsões (6 semanas) | `GET /api/previsoes`, serviço de previsão | 6 semanas retornadas; falha isolada em 503; teste de previsão | API / Modelo |
| **RF004** — treinar/executar o modelo | `scripts/train_model.py`, `models/modelo_rf_v1.joblib`, `docs/grafico_real_x_previsto.png`, `docs/metricas_modelos.md`, `metrica_modelo`/`modelo_preditivo` | Métricas MAE/RMSE/MAPE/acerto; DM/Wilcoxon; `backend/tests/test_model.py` (15 testes) | Modelo |
| **RF004** — registrar métricas (rastreabilidade) | `GET /api/metricas`, `metrica_modelo` no banco | `/api/metricas` reflete as métricas reais; teste de métricas | Modelo |
| Objetivo: qualidade de dados documentada | `docs/relatorio_qualidade_dados.md` | Amarração ISO/IEC 25012 (exatidão/completude/consistência/atualidade) | Dados |
| Objetivo: arquitetura e nuvem documentadas | `docs/arquitetura_descricao.md`, `plano_nuvem.md`, `plano_seguranca.md` | Cobertura da seção 6.8 do Manual (segurança, logs, backup, custos) | Nuvem |
| Objetivo: requisitos rastreáveis e testáveis | `docs/requisitos.md` | Cada RF tem critério de aceite testável | Todos |

Evidências de teste globais: `cd backend && uv run pytest -q` = **32 testes**
(15 modelo + 12 API + 5 ETL).

---

## 7. Limitações e trabalhos futuros

### 7.1 Limitações (protótipo acadêmico)

- **Confirmação por proxy:** ausência dos campos laboratoriais da Tabela 1 do TC2;
  a variável-alvo usa `PCR_FLUASU` preenchido (ISO/IEC 25012 — Exatidão).
- **Série curta e esparsa** com hiato 2020–2021 e muitas semanas de zero casos.
- **Subnotificação e atraso de notificação** (reserva das 8 semanas recentes).
- **Modelo sem superioridade comprovada:** ver seção 5.1.
- **NM_UN_INTE não populado** pela fonte (granularidade sempre municipal).
- **Nuvem e frontend não provisionados** neste ambiente (planejamento documentado).

### 7.2 Trabalhos futuros

- **Frontend Next.js:** dashboard com filtros por período e unidade de notificação,
  cards, gráficos e comparação real × previsto, com previsão **visualmente
  separada** do dado real (RF001/RF002; ISO/IEC 25059).
- **Implantação AWS:** EC2 (API), RDS (PostgreSQL), S3 (backup/artefatos), CORS
  restrito, HTTPS, criptografia em repouso, backup testado (ver
  [`plano_nuvem.md`](plano_nuvem.md) e [`plano_seguranca.md`](plano_seguranca.md)).
- **Reextração dos dados** com os campos de confirmação da Tabela 1, caso
  disponíveis, para substituir a proxy.
- **Retreinamento periódico** do modelo (concept drift) e explicabilidade no
  dashboard.

---

## 8. Referências (ABNT NBR 6023)

As referências abaixo sustentam cada decisão/técnica aplicada no núcleo prático.
Documentos internos do projeto (em `Documentos_Para_Desenv_TCC/`) são citados como
fonte interna; documentações técnicas e normas são citadas com o link de acesso.

### 8.1 Normas técnicas

- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e
  documentação — trabalhos acadêmicos — apresentação. Rio de Janeiro: ABNT, 2011.
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e
  documentação — referências — elaboração. Rio de Janeiro: ABNT, 2018.
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6027**: informação e
  documentação — sumário — apresentação. Rio de Janeiro: ABNT, 2012.
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6028**: informação e
  documentação — resumo, resenha e recensão — apresentação. Rio de Janeiro: ABNT,
  2021.
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10520**: informação e
  documentação — citações em documentos — apresentação. Rio de Janeiro: ABNT, 2023.
- INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL
  COMMISSION. **ISO/IEC 25010:2023** — Systems and software engineering — SQuaRE —
  Product quality model. Geneva: ISO/IEC, 2023. Disponível em:
  [https://www.iso.org/standard/78176.html](https://www.iso.org/standard/78176.html).
  Acesso em: 30 set. 2026.
- INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL
  COMMISSION. **ISO/IEC 25012:2008** — Software engineering — SQuaRE — Data
  quality model. Geneva: ISO/IEC, 2008. Disponível em:
  [https://www.iso.org/standard/35736.html](https://www.iso.org/standard/35736.html).
  Acesso em: 30 set. 2026.
- INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL
  COMMISSION. **ISO/IEC 25059:2023** — SQuaRE — Quality model for AI systems.
  Geneva: ISO/IEC, 2023. Disponível em:
  [https://www.iso.org/standard/80655.html](https://www.iso.org/standard/80655.html).
  Acesso em: 30 set. 2026.
- INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL
  COMMISSION. **ISO/IEC 27002:2022** — Information security, cybersecurity and
  privacy protection — Information security controls. Geneva: ISO/IEC, 2022.
  Disponível em:
  [https://www.iso.org/standard/75652.html](https://www.iso.org/standard/75652.html).
  Acesso em: 30 set. 2026.

### 8.2 Fonte de dados

- BRASIL. Ministério da Saúde. **SIVEP-Gripe — Dados de Síndrome Respiratória
  Aguda Grave (SRAG)**. Portal de Dados Abertos do SUS (openDataSUS). Disponível
  em: [https://opendatasus.saude.gov.br/](https://opendatasus.saude.gov.br/).
  Acesso em: 30 set. 2026.
- BRASIL. **Lei nº 13.709, de 14 de agosto de 2018**. Lei Geral de Proteção de
  Dados Pessoais (LGPD). Brasília, 2018.

### 8.3 Bibliotecas e ferramentas (parte aplicada)

- TIANGOLO, Sebastián. **FastAPI documentation**. Disponível em:
  [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/). Acesso em:
  30 set. 2026. — *(API REST, RF001/RF002/RF003)*
- SCIKIT-LEARN DEVELOPERS. **RandomForestRegressor**. Disponível em:
  [https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).
  Acesso em: 30 set. 2026. — *(modelo principal, RF004)*
- STATSMODELS DEVELOPERS. **SARIMAX**. Disponível em:
  [https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html).
  Acesso em: 30 set. 2026. — *(comparador SARIMA)*
- META (FACEBOOK). **Prophet: forecasting at scale**. Disponível em:
  [https://facebook.github.io/prophet/](https://facebook.github.io/prophet/).
  Acesso em: 30 set. 2026. — *(comparador Prophet)*
- THE PANDAS DEVELOPMENT TEAM. **pandas documentation**. Disponível em:
  [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/). Acesso em:
  30 set. 2026. — *(ETL / manipulação de dados)*
- HARRIS, C. R. et al. **NumPy documentation**. Disponível em:
  [https://numpy.org/doc/](https://numpy.org/doc/). Acesso em: 30 set. 2026. —
  *(cálculo numérico)*
- JOBLIB DEVELOPERS. **joblib documentation**. Disponível em:
  [https://joblib.readthedocs.io/](https://joblib.readthedocs.io/). Acesso em:
  30 set. 2026. — *(serialização do modelo, `.joblib`)*
- SQLALCHEMY DEVELOPERS. **SQLAlchemy 2.0 documentation**. Disponível em:
  [https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/). Acesso
  em: 30 set. 2026. — *(camada de acesso a dados)*
- POSTGRESQL GLOBAL DEVELOPMENT GROUP. **PostgreSQL documentation**. Disponível
  em: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/). Acesso
  em: 30 set. 2026. — *(banco relacional, RF003)*

### 8.4 Literatura das técnicas empregadas

- BREIMAN, Leo. Random Forests. **Machine Learning**, v. 45, n. 1, p. 5-32, 2001.
  — *(Random Forest)*
- DIEBOLD, Francis X.; MARIANO, Roberto S. Comparing Predictive Accuracy.
  **Journal of Business & Economic Statistics**, v. 13, n. 3, p. 253-263, 1995. —
  *(teste de Diebold-Mariano)*
- HARVEY, David; LEYBOURNE, Stephen; NEWBOLD, Paul. Testing the equality of
  prediction mean squared errors. **International Journal of Forecasting**, v. 13,
  n. 2, p. 281-291, 1997. — *(correção de amostra pequena do DM)*
- WILCOXON, Frank. Individual Comparisons by Ranking Methods. **Biometrics
  Bulletin**, v. 1, n. 6, p. 80-83, 1945. — *(teste de Wilcoxon)*
- HYNDMAN, Rob J.; KOEHLER, Anne B. Another look at measures of forecast accuracy.
  **International Journal of Forecasting**, v. 22, n. 4, p. 679-688, 2006. —
  *(MAPE/sMAPE)*
- HYNDMAN, Rob J.; ATHANASOPOULOS, George. **Forecasting: Principles and
  Practice**. 3. ed. Melbourne: OTexts, 2021. Disponível em:
  [https://otexts.com/fpp3/](https://otexts.com/fpp3/). Acesso em: 30 set. 2026. —
  *(validação cronológica walk-forward)*
- TAYLOR, Sean J.; LETHAM, Benjamin. Forecasting at scale. **The American
  Statistician**, v. 72, n. 1, p. 37-45, 2018. — *(Prophet)*

### 8.5 Documentos internos do projeto (fonte de decisões)

- **Manual Interno de Desenvolvimento do TCC (v2)** —
  `Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx`.
  *(delimitações, módulos, KPIs seção 9.2, template de requisito 10.1, seção 6.8)*
- **TCC — C D H M (TC2)** — `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx`.
  *(requisitos RF001–RF004, Tabela 1 de variáveis, tabelas do banco)*
- **Anexo de Qualidade ISO/IEC 25000 v4** —
  `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`.
  *(mapeamento ISO/IEC 25010/25012/25059/27002)*
- **Definição Conceitual do Projeto v12** —
  `Documentos_Para_Desenv_TCC/TCC_DefinicaoConceitual_v12 (1).docx`.
  *(escopo, hipóteses, metas)*
- **Manual Padrão de Documentação de Bancos de Dados** —
  `Documentos_Para_Desenv_TCC/Manual_Padrao_Documentacao_Bancos_de_Dados.docx`.
  *(nomenclatura e dicionário de banco)*
- **Normas CNPq sobre uso de IA** —
  `Documentos_Para_Desenv_TCC/Normas CNPQ Uso de IA.pdf`. *(registro do uso de IA
  no desenvolvimento)*

> Todas as afirmações de resultado neste documento possuem evidência (métrica,
> tabela, gráfico ou teste), conforme a Definition of Done do Manual Interno
> (seção 8).
