# Especificação de Requisitos

> Documento de requisitos do núcleo prático do TCC "Análise preditiva de
> Influenza A no município de São Paulo utilizando IA com dados do SIVEP-Gripe".
> Segue o template de requisito da seção 10.1 do Manual Interno de
> Desenvolvimento. Protótipo acadêmico de apoio à visualização, análise
> exploratória e previsão de dados epidemiológicos; **não** é ferramenta oficial
> de vigilância nem substituto de plataformas governamentais.

## 1. Atores

Os atores foram separados conforme a orientação da seção 6.1 do Manual (não
tratar usuário comum, equipe técnica e DATASUS como o mesmo ator):

| Ator | Papel |
| ---- | ----- |
| **Usuário comum** | Consulta o dashboard e as previsões (somente leitura). No núcleo prático desta entrega, consome a API REST. |
| **Administrador / equipe técnica** | Executa ETL, treina o modelo, mantém o banco e a API, opera rotas administrativas (previstas para fase futura). |
| **DATASUS / SIVEP-Gripe** | Fonte externa dos dados públicos de SRAG. Não interage com o sistema em tempo de execução; fornece o arquivo consolidado. |

## 2. Convenções e decisões de escopo propagadas

Conforme o Manual (seções 3, 7.1 e checklist 9.1) e o relatório de qualidade de
dados, as decisões abaixo são propagadas por todos os requisitos:

- **Recorte geográfico:** sempre **município de São Paulo** (CO_MUN_RES = 355030).
  Nunca "estado de São Paulo" nem "cidade" genérica.
- **Granularidade de consulta:** por **unidade de notificação** (campo
  `NM_UN_INTE`), **não** por bairro/região (o SIVEP-Gripe/SINAN não disponibiliza
  bairro). A modelagem preditiva é **exclusivamente municipal**; o filtro por
  unidade vale só para consulta/visualização histórica.
- **Pendência de dados (NM_UN_INTE):** a fonte consolidada atual **não popula**
  `NM_UN_INTE`. A estrutura existe (tabela `unidade_notificacao`), mas o campo fica
  registrado como pendência documentada (ver `docs/relatorio_qualidade_dados.md` e
  `docs/dicionario_banco.md`).
- **Confirmação de Influenza A por proxy:** os campos de confirmação laboratorial
  da Tabela 1 do TC2 (`CLASSI_FIN`, `PCR_RESUL`, `POS_PCRFLU`, `TP_FLU_PCR`,
  `POS_AN_FLU`, `TP_FLU_AN`) **não existem** no arquivo. Usa-se `PCR_FLUASU`
  preenchido como **proxy de confirmação** (regra documentada, campos ausentes não
  fabricados).

## 3. Requisitos funcionais

O template segue a seção 10.1 do Manual. O estado de implementação reflete o que
foi efetivamente construído nesta entrega (ETL + banco + backend + modelo). O
frontend (dashboard Next.js) é **fase seguinte** — por isso RF001/RF002 estão
atendidos na camada de API, com a apresentação visual planejada.

### RF001 — Visualizar e consultar dados epidemiológicos de Influenza A

| Campo | Conteúdo |
| ----- | -------- |
| **Código** | RF001 |
| **Nome** | Visualizar e consultar dados históricos de Influenza A |
| **Descrição** | O sistema deve permitir consultar os dados históricos de casos-proxy de Influenza A no **município de São Paulo**, por período e (quando a fonte popular) por unidade de notificação. |
| **Ator** | Usuário comum |
| **Entradas** | Período de referência (semana epidemiológica e ano de início e fim) e, opcionalmente, unidade de notificação (`NM_UN_INTE`) dentro do município de São Paulo. Na ausência de seleção, retorna o período mais recente disponível. |
| **Processamento** | A API consulta a série temporal no banco (via camada de repositórios), valida o intervalo (`início <= fim`, semana no domínio 1–53) e agrega os dados. |
| **Saída** | Série semanal filtrada em JSON padronizado (`{sucesso, dados, mensagem}`); no dashboard futuro, gráficos/cards/tabelas. |
| **Pré-condição** | Dados históricos disponíveis e íntegros no banco (RF003). API acessível. |
| **Pós-condição** | Retorna os dados do filtro selecionado ou o período mais recente quando nenhum filtro é aplicado. |
| **Critério de aceite** | Os endpoints `GET /api/dados` e `GET /api/series-temporais` retornam dados reais do banco; intervalo inválido retorna erro tratado (400/422). Coberto por `backend/tests/test_api.py`. |
| **Estado** | Atendido na API (FEAT-003). Dashboard visual planejado (fase futura). |

### RF002 — Exibir previsões de incidência de Influenza A

| Campo | Conteúdo |
| ----- | -------- |
| **Código** | RF002 |
| **Nome** | Exibir previsões de incidência de Influenza A |
| **Descrição** | O sistema deve disponibilizar estimativas preditivas de incidência de Influenza A para as **6 semanas subsequentes** ao período histórico analisado, no município de São Paulo. |
| **Ator** | Usuário comum |
| **Entradas** | Histórico disponível no banco (desde 2009), opcionalmente o horizonte (padrão 6 semanas). |
| **Processamento** | O serviço de previsão carrega o modelo `.joblib` em memória e gera a previsão recursiva de 6 semanas; se o modelo estiver indisponível, usa baseline sazonal e isola a falha (não derruba RF001). |
| **Saída** | Previsão de 6 semanas em JSON padronizado, com identificação da origem (`modelo_treinado`/`baseline`). No dashboard futuro, previsão **visualmente separada** do dado real. |
| **Pré-condição** | Modelo treinado e serializado (RF004) e/ou série de treino no banco (RF003). |
| **Pós-condição** | Retorna as estimativas ou `503` (previsão indisponível) sem afetar os dados históricos. |
| **Critério de aceite** | `GET /api/previsoes` retorna 6 semanas; falha do módulo preditivo isolada em `503`. Coberto por `backend/tests/test_api.py`. |
| **Estado** | Atendido na API (FEAT-003/FEAT-004). Indicação visual de "estimativa" prevista no dashboard futuro (ISO/IEC 25059 — Segurança Operacional). |

### RF003 — Coletar e processar os dados epidemiológicos do SIVEP-Gripe

| Campo | Conteúdo |
| ----- | -------- |
| **Código** | RF003 |
| **Nome** | Coletar e processar os dados epidemiológicos do SIVEP-Gripe |
| **Descrição** | O sistema deve coletar os dados públicos do SIVEP-Gripe/SINAN, preservar a base bruta, tratar inconsistências, gerar a série temporal semanal do município de São Paulo e persistir no banco relacional. |
| **Ator** | Administrador / equipe técnica (com o DATASUS como fonte externa) |
| **Entradas** | Arquivo CSV consolidado (`Dados consolidados e padronizados 2009 a 2019 e 2022 a 2026.csv`), encoding UTF-8 com BOM, separador `;`. |
| **Processamento** | ETL: preserva a base bruta em `data/raw/`; filtra o município (355030); deriva ano e semana epidemiológica; aplica a regra de proxy `PCR_FLUASU`; quantifica ausentes/duplicidades; gera a série semanal contínua; reserva as 8 semanas mais recentes; carrega o banco. |
| **Saída** | `data/processed/base_tratada.csv`, `data/processed/serie_temporal_semanal.csv`, banco PostgreSQL populado (schema/seed). |
| **Pré-condição** | Ambiente Python configurado (uv); arquivo-fonte disponível. |
| **Pós-condição** | Base tratada e série temporal geradas e documentadas; base bruta intacta. |
| **Critério de aceite** | ETL produz 13.139 registros de SP e série semanal contínua com as 8 semanas recentes marcadas; `backend/tests/test_etl.py` passa. |
| **Estado** | Atendido (FEAT-001, FEAT-002). |

### RF004 — Treinar e executar o modelo preditivo de Influenza A

| Campo | Conteúdo |
| ----- | -------- |
| **Código** | RF004 |
| **Nome** | Treinar e executar o modelo preditivo de Influenza A |
| **Descrição** | O sistema deve treinar, validar e disponibilizar o modelo preditivo (Random Forest) para estimar casos de Influenza A nas 6 semanas subsequentes, comparado a baseline, SARIMA e Prophet sob validação cronológica, com teste de significância. |
| **Ator** | Administrador / equipe técnica |
| **Entradas** | Série temporal semanal de treino (semanas com `USAR_NO_TREINO = True`). |
| **Processamento** | Engenharia de atributos temporais; walk-forward (origem expansiva, horizonte 6); baseline + SARIMA + Prophet no mesmo protocolo; MAE/RMSE/MAPE/sMAPE/acerto direcional; Diebold-Mariano e Wilcoxon; serialização e registro no banco. |
| **Saída** | `models/modelo_rf_v1.joblib`, `docs/grafico_real_x_previsto.png`, `docs/metricas_modelos.md/.csv`, registros em `modelo_preditivo`/`metrica_modelo`. |
| **Pré-condição** | Série temporal disponível e íntegra (RF003); bibliotecas instaladas. |
| **Pós-condição** | Modelo treinado, versionado e integrado ao backend; métricas registradas. |
| **Critério de aceite** | `scripts/train_model.py` gera todos os artefatos; MAE/RMSE/MAPE e acerto direcional calculados; teste de significância aplicado e reportado com honestidade; `backend/tests/test_model.py` passa. |
| **Estado** | Atendido (FEAT-004). O modelo **não** foi apresentado como comprovadamente superior (ver `docs/documentacao_modelo.md`, seção 8). |

## 4. Requisitos não funcionais

Derivados do Anexo de Qualidade ISO/IEC 25000 v4 (25010/25012/25059) e ISO/IEC
27002. A rastreabilidade completa (característica × critério × validação) está em
[`docs/documentacao_projeto.md`](documentacao_projeto.md), seção 6.

| Código | Requisito não funcional | Norma / característica | Como validar |
| ------ | ----------------------- | --------------------- | ------------ |
| RNF001 | Endpoints principais respondem em até 2 s em ambiente de teste. | ISO/IEC 25010 — Eficiência de desempenho (Comportamento temporal) | Medição de tempo de resposta / logs |
| RNF002 | Retorno JSON padronizado e reaproveitável (`{sucesso, dados, mensagem}`). | ISO/IEC 25010 — Compatibilidade (Interoperabilidade) | Validação de contrato/schema; testes de API |
| RNF003 | Tratamento de erros para parâmetros inválidos, sem vazar stack trace. | ISO/IEC 25010 — Adequação funcional / Capacidade de interação (Assistência ao usuário) | Testes de intervalo inválido (400/422) |
| RNF004 | Falha do módulo preditivo não interrompe a consulta de dados (RF001). | ISO/IEC 25010 — Confiabilidade (Tolerância a falhas) | Teste de cenário de falha (503 isolado) |
| RNF005 | Arquitetura em camadas (rotas/serviços/repositórios/modelos/schemas). | ISO/IEC 25010 — Manutenibilidade (Modularidade/Modificabilidade) | Revisão de arquitetura e de código |
| RNF006 | Logs estruturados com timestamp, origem e nível; `log_processamento` no banco. | ISO/IEC 25010 — Manutenibilidade (Analisabilidade); ISO/IEC 27002 (8.15/8.16) | Revisão de logs |
| RNF007 | Camada de acesso a dados portável (PostgreSQL/RDS ↔ SQLite). | ISO/IEC 25010 — Flexibilidade (Capacidade de substituição) | Testes em SQLite; DDL no PostgreSQL |
| RNF008 | Credenciais fora do código-fonte, lidas de variável de ambiente. | ISO/IEC 27002 (8.24 / segregação de segredos) | Revisão do `.env.example` e do repositório |
| RNF009 | Qualidade de dados: exatidão/completude/consistência/atualidade tratadas e documentadas. | ISO/IEC 25012 | `docs/relatorio_qualidade_dados.md` |
| RNF010 | Previsões identificadas como estimativa (não dado real). | ISO/IEC 25059 — Segurança Operacional (Alerta de perigo) | Origem da previsão na API; indicação visual (dashboard futuro) |
| RNF011 | Nenhuma ação automática de saúde pública; somente leitura para previsões. | ISO/IEC 25059 — Segurança Operacional (Restrição operacional); Controlabilidade | Revisão de escopo funcional |
| RNF012 | Uso exclusivo de dados agregados por semana/localidade (minimização — LGPD). | ISO/IEC 25012 (Conformidade) / LGPD | Revisão do schema de resposta |

## 5. Rastreabilidade

A matriz que amarra cada RF e objetivo específico ao entregável e à evidência de
validação está no documento consolidado
[`docs/documentacao_projeto.md`](documentacao_projeto.md), seção 6.6. As referências
completas no padrão ABNT (NBR 6023) estão na seção 8 do mesmo documento.
