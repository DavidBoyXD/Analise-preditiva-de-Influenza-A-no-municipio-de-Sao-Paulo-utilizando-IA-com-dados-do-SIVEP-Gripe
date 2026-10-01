# Análise preditiva de Influenza A no município de São Paulo utilizando inteligência artificial com base em dados epidemiológicos do SIVEP-Gripe

> **Natureza deste documento.** Material de apoio redigido como base para integração ao TC2 do grupo. Documento NOVO e separado: não substitui o trabalho autoral do grupo (`Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx`) nem a documentação técnica consolidada (`docs/documentacao_projeto.md`). Reúne, em formato acadêmico ABNT e em Português-Brasil, a redação dos capítulos espelhando a estrutura do TC2, com os números efetivamente apurados no núcleo prático e com a análise exploratória complementar do recorte intramunicipal por distrito.
>
> **Posicionamento (inegociável).** Este é um **protótipo acadêmico** de apoio à visualização, análise exploratória e previsão de dados epidemiológicos. Não é ferramenta oficial de vigilância, não substitui plataformas governamentais e não comprova melhoria direta em decisões de saúde pública. Todas as afirmações de resultado possuem evidência (métrica, tabela, gráfico ou teste).

---

## Folha de rosto (esqueleto ABNT NBR 14724)

**Instituição:** Universidade Paulista (UNIP)
**Curso:** Ciência da Computação
**Local e ano:** São Paulo, 2026

**Título:** Análise preditiva de Influenza A no município de São Paulo utilizando inteligência artificial com base em dados epidemiológicos do SIVEP-Gripe

**Integrantes:**
- Carlos Henrique Santana Rodrigues *(RA: PLACEHOLDER, confirmar com o grupo)*
- David Andrew Deziderio Gomes Silva *(RA: PLACEHOLDER, confirmar com o grupo)*
- Henrique Vitale Cassú *(RA: PLACEHOLDER, confirmar com o grupo)*
- Marcelo Augusto de Souza Silva *(RA: PLACEHOLDER, confirmar com o grupo)*

**Orientadora:** Stephany Oliveira

> **Placeholders a confirmar pelo grupo** (não preenchidos aqui por dependerem de dados pessoais e institucionais): números de RA/matrícula, dedicatória, agradecimentos, epígrafe, data exata de entrega, folha de aprovação com assinaturas da banca. A ficha catalográfica, quando exigida, segue o modelo da biblioteca da instituição.

---

## Resumo

O presente trabalho descreve o desenvolvimento de um protótipo acadêmico para análise temporal e previsão de casos de Influenza A no município de São Paulo, a partir de dados públicos do SIVEP-Gripe (subsistema do DATASUS) de Síndrome Respiratória Aguda Grave (SRAG). O sistema abrange todo o fluxo de dados: extração, transformação e carga (ETL) dos microdados, armazenamento em banco relacional PostgreSQL em Terceira Forma Normal, disponibilização por uma interface de programação de aplicações (API REST) construída em FastAPI e um painel web (dashboard) em Next.js para consulta e visualização. O problema foi delimitado de forma objetiva: série semanal municipal (semana epidemiológica), período de 2009 a 2019 e de 2022 a 2026 (com hiato deliberado em 2020 e 2021), variável-alvo definida por uma regra de proxy sobre o campo PCR_FLUASU, horizonte preditivo de 6 semanas e critério de sucesso mensurável. O modelo preditivo principal (Random Forest) foi comparado a um baseline sazonal-ingênuo, ao SARIMA e ao Prophet sob validação cronológica walk-forward, com métricas de erro (MAE, RMSE, MAPE, sMAPE) e acerto direcional, além de testes de significância (Diebold-Mariano e Wilcoxon). Os resultados foram reportados com honestidade metodológica: nesta série curta e esparsa, o Random Forest não superou o baseline em MAE e RMSE, o teste de Diebold-Mariano não indicou vantagem estatisticamente significativa, e o SARIMA obteve o menor MAE. O modelo é entregue por completude do escopo, com desempenho relatado de forma transparente, não como comprovadamente superior. Como análise exploratória complementar, investigou-se um recorte intramunicipal por distrito, derivado do endereço público do hospital notificante por meio do cadastro CNES e das camadas territoriais do GeoSampa; trata-se de prova de conceito validada apenas no ano de 2024 (90,0% dos casos da capital resolvidos a um distrito), com a limitação central de que o distrito identificado é o do hospital, e não o da residência do paciente.

**Palavras-chave:** inteligência artificial; previsão; Influenza A; epidemiologia; SIVEP-Gripe; séries temporais.

---

## Abstract

This work describes the development of an academic prototype for the temporal analysis and forecasting of Influenza A cases in the municipality of São Paulo, based on public data from SIVEP-Gripe (a subsystem of DATASUS) regarding Severe Acute Respiratory Syndrome (SARS). The system covers the entire data flow: extraction, transformation and loading (ETL) of the microdata, storage in a relational PostgreSQL database in Third Normal Form, exposure through a REST application programming interface (API) built with FastAPI, and a web dashboard in Next.js for querying and visualization. The problem was clearly scoped: a weekly municipal series (epidemiological week), a period from 2009 to 2019 and from 2022 to 2026 (with a deliberate gap in 2020 and 2021), a target variable defined by a proxy rule over the PCR_FLUASU field, a 6-week forecasting horizon, and a measurable success criterion. The main predictive model (Random Forest) was compared with a seasonal-naive baseline, SARIMA and Prophet under walk-forward cross-validation, using error metrics (MAE, RMSE, MAPE, sMAPE) and directional accuracy, plus significance tests (Diebold-Mariano and Wilcoxon). Results were reported with methodological honesty: on this short and sparse series, the Random Forest did not outperform the baseline in MAE and RMSE, the Diebold-Mariano test did not indicate a statistically significant advantage, and SARIMA achieved the lowest MAE. The model is delivered for completeness of scope, with its performance reported transparently, not as proven superior. As a complementary exploratory analysis, an intra-municipal breakdown by district was investigated, derived from the public address of the reporting hospital through the CNES registry and the GeoSampa territorial layers; it is a proof of concept validated only for the year 2024 (90.0% of the capital's cases resolved to a district), with the central limitation that the identified district is the hospital's, not the patient's residence.

**Keywords:** artificial intelligence; forecasting; Influenza A; epidemiology; SIVEP-Gripe; time series.

---

## Sumário

1. Introdução
2. Objetivos
3. Revisão de literatura
4. Material e método
5. Resultados
6. Considerações finais
- Referências
- Apêndices e anexos
- Declaração de uso de inteligência artificial

---

## 1 Introdução

A Influenza A é um vírus respiratório de ampla circulação, com forte sazonalidade e potencial epidêmico recorrente. A Organização Mundial da Saúde estima que as epidemias sazonais de influenza estejam associadas a cerca de 290.000 a 650.000 mortes por ano no mundo decorrentes de complicações respiratórias (WHO, 2021). No Brasil, os casos graves de síndromes respiratórias são acompanhados pela vigilância da Síndrome Respiratória Aguda Grave (SRAG), cujos registros são consolidados pelo SIVEP-Gripe, subsistema do DATASUS, e disponibilizados publicamente no Portal de Dados Abertos do SUS (BRASIL, Ministério da Saúde). Esses microdados constituem uma fonte rica, porém de interpretação delicada: trazem subnotificação, atraso de notificação, variações de preenchimento e granularidade geográfica limitada, o que exige cuidado metodológico ao transformá-los em séries analisáveis.

### 1.1 Delimitação do problema

Em resposta direta à necessidade de um problema bem delimitado, este trabalho fixa, de forma objetiva e verificável, os seguintes contornos:

- **Recorte geográfico:** município de São Paulo (campo CO_MUN_RES igual a 355030), nunca o estado nem a cidade de forma genérica.
- **Período:** 2009 a 2019 (SINAN harmonizado) e 2022 em diante (SIVEP-Gripe), com hiato deliberado em 2020 e 2021 (ausente na fonte, não preenchido com zeros artificiais).
- **Granularidade:** série temporal semanal (semana epidemiológica).
- **Variável-alvo:** contagem semanal de casos-proxy de Influenza A no município de São Paulo (regra de proxy detalhada na seção 4.3).
- **Horizonte preditivo:** 6 semanas subsequentes.
- **Baseline:** modelo simples de referência (sazonal-ingênuo).
- **Critério de sucesso mensurável:** registrar MAE, RMSE, MAPE/sMAPE e acerto direcional; comparar com baseline, SARIMA e Prophet sob validação cronológica walk-forward; aplicar teste de significância (Diebold-Mariano e Wilcoxon); e apresentar gráfico real versus previsto. O resultado é mensurável, não narrativo.

### 1.2 Justificativa

O protótipo busca exercitar, de ponta a ponta, um fluxo de ciência de dados aplicado a dados epidemiológicos públicos: coleta, tratamento, modelagem relacional, disponibilização por API e visualização. O valor acadêmico está na integração dessas etapas sob critérios explícitos de qualidade (normas ISO/IEC 25010, 25012, 25059 e 27002) e na avaliação honesta do desempenho preditivo. Importa deixar claro o enquadramento: trata-se de protótipo acadêmico de apoio à visualização, análise exploratória e previsão. O sistema não é ferramenta oficial de vigilância, não substitui plataformas governamentais e não comprova, por si, melhoria em decisões de saúde pública. Essa postura responde diretamente à crítica, recebida na avaliação do TC1, de promessas excessivas sobre apoio à saúde pública sem comprovação: toda afirmação de utilidade é apresentada como hipótese de aplicação futura, condicionada a validação adicional.

### 1.3 Granularidade geográfica e o recorte intramunicipal

Em versões anteriores do planejamento cogitou-se uma análise por bairro. O SIVEP-Gripe/SINAN, contudo, não disponibiliza o bairro de residência do paciente, e o arquivo consolidado adotado no núcleo prático não popula o campo de unidade de notificação (NM_UN_INTE). Por isso, a modelagem preditiva é sempre municipal. O recorte intramunicipal por distrito foi reposicionado como análise exploratória complementar (seção 4.9 e 5.3): derivado do endereço público do hospital notificante por meio do cadastro CNES e das camadas territoriais do GeoSampa, ele é tratado como prova de conceito, com limitações explícitas, e não como parte do núcleo preditivo.

---

## 2 Objetivos

### 2.1 Objetivo geral

Desenvolver um protótipo acadêmico de sistema para análise temporal e previsão de casos de Influenza A no município de São Paulo, utilizando técnicas de inteligência artificial e séries temporais sobre dados públicos do SIVEP-Gripe (DATASUS), com fluxo completo de coleta, armazenamento, disponibilização por API e visualização.

### 2.2 Objetivos específicos

Cada objetivo específico está amarrado a um entregável e a uma métrica ou critério verificável, respondendo à crítica de objetivos sem métricas recebida no TC1.

| # | Objetivo específico | Entregável | Métrica / critério verificável |
| - | ------------------- | ---------- | ------------------------------ |
| a | Coletar e tratar os dados do SIVEP-Gripe | Scripts de ETL e artefatos processados | 13.139 registros do município de São Paulo filtrados de 48.775; série semanal contínua de 832 semanas; 8 semanas recentes reservadas por atraso de notificação |
| b | Modelar e implementar o banco relacional | DDL, índices e dicionário de banco | 9 tabelas em Terceira Forma Normal, validadas em PostgreSQL 16, com 0 chaves estrangeiras órfãs e 0 tabelas/colunas sem comentário |
| c | Desenvolver a API REST | Backend FastAPI em camadas | 6 endpoints com contrato JSON `{sucesso, dados, mensagem}`, validação de intervalo e meta de resposta de até 2 segundos em ambiente de teste |
| d | Treinar e avaliar o modelo preditivo | Modelo serializado e tabela de métricas | MAE, RMSE, MAPE/sMAPE e acerto direcional sob walk-forward, comparados a baseline, SARIMA e Prophet, com Diebold-Mariano e Wilcoxon |
| e | Construir o dashboard web | Frontend Next.js | Atendimento de RF001 e RF002, com lint e build validados sem erros |
| f | Realizar análise exploratória do recorte intramunicipal | Crosswalk hospital para distrito e relatório de cobertura | Prova de conceito em 2024: 90,0% dos casos da capital resolvidos a um distrito; limitações declaradas |

---

## 3 Revisão de literatura

### 3.1 Contextualização epidemiológica e o SIVEP-Gripe

A vigilância da SRAG no Brasil estrutura-se sobre a notificação compulsória de casos graves, consolidada no SIVEP-Gripe. Os microdados abertos permitem reconstruir séries temporais de casos, mas carregam características que precisam ser discutidas criticamente (seção 3.4). A distinção entre SRAG, de perfil hospitalar e mais grave, e a Síndrome Gripal (SG), de perfil ambulatorial, é relevante: a série analisada reflete casos graves notificados, não a totalidade da circulação viral na população.

### 3.2 Modelos de previsão de séries temporais

A literatura oferece diferentes famílias de modelos, cada uma com vantagens e limitações para séries epidemiológicas curtas e esparsas.

- **ARIMA e SARIMA:** modelos estatísticos clássicos que capturam autocorrelação e, no caso sazonal (SARIMA), componentes periódicos. Dependem de estacionariedade (após diferenciação) e de uma sazonalidade bem definida. São interpretáveis e parcimoniosos, mas sensíveis a séries ruidosas e a mudanças de regime (HYNDMAN; ATHANASOPOULOS, 2021).
- **Prophet:** modelo de decomposição aditiva (tendência, sazonalidade e feriados) proposto por Taylor e Letham (2018), robusto a dados faltantes e a múltiplas sazonalidades, de ajuste simples. Pode, porém, suavizar demais picos abruptos típicos de surtos.
- **LSTM e redes recorrentes:** abordagens de aprendizado profundo capazes de modelar dependências temporais longas e não lineares, ao custo de exigirem volume de dados considerável e ajuste cuidadoso, condição raramente satisfeita em séries epidemiológicas municipais curtas.
- **Random Forest:** ensemble de árvores de decisão (BREIMAN, 2001) que lida bem com não linearidades e interações entre atributos, mas não extrapola tendência além da faixa observada no treino, o que é uma limitação relevante para previsão de picos crescentes.
- **XGBoost:** método de boosting de árvores, frequentemente competitivo em dados tabulares, com desempenho forte quando há volume e boa engenharia de atributos, novamente limitado quanto à extrapolação de tendência.

A escolha do Random Forest como modelo principal, com engenharia de atributos temporais, apoia-se na sua robustez a não linearidades e na facilidade de uso sobre atributos derivados (lags, médias móveis e sazonalidade). A comparação sistemática com baseline, SARIMA e Prophet garante que o desempenho seja lido em contexto, e não isoladamente.

### 3.3 Avaliação de previsões e testes de significância

A avaliação segue boas práticas de previsão: métricas de erro absoluto (MAE) e quadrático (RMSE), percentuais (MAPE restrito a semanas positivas e sMAPE, finito mesmo com zeros), conforme discutido por Hyndman e Koehler (2006), e acerto direcional. A validação é cronológica (walk-forward de origem expansiva), nunca aleatória, respeitando a ordem temporal (HYNDMAN; ATHANASOPOULOS, 2021). A significância das diferenças de acurácia é verificada pelo teste de Diebold-Mariano (DIEBOLD; MARIANO, 1995), com a correção de amostra pequena de Harvey, Leybourne e Newbold (1997), e pelo teste não paramétrico de Wilcoxon (WILCOXON, 1945) sobre os erros absolutos.

### 3.4 Qualidade dos dados públicos do DATASUS

A utilização responsável dos microdados exige discutir suas limitações, em resposta à crítica do TC1 sobre a ausência dessa análise:

- **Subnotificação:** nem todos os casos chegam ao sistema, e o perfil hospitalar da SRAG subestima a circulação total do vírus.
- **Atraso de notificação:** registros recentes ainda estão em maturação; por isso, as 8 semanas epidemiológicas mais recentes são reservadas e não entram no treino.
- **Sazonalidade e esparsidade:** há forte sazonalidade anual e grande número de semanas com zero casos, o que afeta métricas percentuais e a estabilidade dos modelos.
- **Viés de preenchimento e consistência:** campos de texto livre (como o nome da unidade) e mudanças de codificação ao longo dos anos introduzem inconsistências que exigem normalização e documentação.
- **Granularidade geográfica:** a fonte desce ao município de residência, não ao bairro, o que motiva o tratamento municipal da série e o reposicionamento do recorte por distrito como análise exploratória.

### 3.5 Trabalhos relacionados

O trabalho dialoga com a literatura de previsão de doenças respiratórias por séries temporais e aprendizado de máquina, bem como com estudos que empregam dados abertos de vigilância. O diferencial proposto é a combinação de um fluxo completo de engenharia de dados e software com avaliação estatística honesta do ganho preditivo, somada à investigação exploratória de um recorte territorial derivado de dados cadastrais públicos.

---

## 4 Material e método

### 4.1 Tipo de pesquisa e hipótese

A pesquisa é aplicada, de natureza quantitativa e caráter exploratório-experimental: constrói-se um artefato de software e avalia-se empiricamente seu desempenho preditivo. A hipótese de trabalho é que a incorporação de atributos temporais (defasagens, médias móveis e sazonalidade) a um modelo de aprendizado de máquina possa produzir previsões de curto prazo competitivas frente a um baseline sazonal. Essa hipótese é testada, e seu resultado é reportado tal como observado, inclusive quando não confirmada.

### 4.2 Delimitações de escopo

Reafirmam-se as delimitações da seção 1.1: recorte no município de São Paulo (CO_MUN_RES igual a 355030); período de 2009 a 2019 e de 2022 a 2026, com hiato deliberado em 2020 e 2021 (não preenchido com zeros); granularidade semanal; variável-alvo de casos-proxy de Influenza A; horizonte de 6 semanas; baseline sazonal-ingênuo; e modelagem sempre municipal. A granularidade de consulta por unidade de notificação (NM_UN_INTE) permanece registrada como estrutura, mas não é populada pela fonte atual.

### 4.3 Fonte e tratamento de dados (ETL)

O arquivo-fonte é `Dados consolidados e padronizados 2009 a 2019 e 2022 a 2026.csv` (48.775 registros, codificação UTF-8 com BOM, separador ponto e vírgula). A base bruta é preservada em cópia fiel, nunca sobrescrita. O ETL filtra o município de São Paulo (13.139 de 48.775 registros), deriva ANO e SEMANA_EPI a partir de DT_SIN_PRI/SEM_PRI, e gera uma série temporal semanal contínua de 832 semanas (semanas sem casos recebem zero; os anos ausentes de 2020 e 2021 não são preenchidos com zeros artificiais). As 8 semanas epidemiológicas mais recentes são marcadas como reservadas (atraso de notificação) e excluídas do treino.

**Limitação honesta da variável-alvo (proxy PCR_FLUASU).** Os campos de confirmação laboratorial previstos na Tabela 1 do TC2 (CLASSI_FIN, PCR_RESUL, POS_PCRFLU, TP_FLU_PCR, POS_AN_FLU e TP_FLU_AN) não existem no arquivo consolidado. Adota-se a regra de proxy: um registro com PCR_FLUASU preenchido conta como caso-proxy de Influenza A. Os campos ausentes não foram fabricados. Essa decisão é amarrada à ISO/IEC 25012 (Exatidão e Consistência).

**Tabela 1: Variáveis de interesse (reproduzida do TC2).**

| Campo | Papel no estudo |
| ----- | --------------- |
| CO_MUN_RES | Restrição geográfica (município de São Paulo, 355030) |
| DT_SIN_PRI | Indexador temporal (data dos primeiros sintomas) |
| CLASSI_FIN | Classificação final (ausente no CSV consolidado) |
| PCR_RESUL | Resultado de PCR (ausente no CSV consolidado) |
| POS_PCRFLU | Positividade de PCR para influenza (ausente no CSV consolidado) |
| TP_FLU_PCR | Tipo de influenza por PCR (ausente no CSV consolidado) |
| PCR_FLUASU | Subtipo de influenza A (único campo presente; usado como proxy) |
| POS_AN_FLU | Positividade por antígeno (ausente no CSV consolidado) |
| TP_FLU_AN | Tipo de influenza por antígeno (ausente no CSV consolidado) |

### 4.4 Banco de dados

O banco é relacional, em Terceira Forma Normal (3FN), com 9 tabelas e nomenclatura padronizada (chave primária `id_<entidade>`, chave estrangeira `id_<entidade_referenciada>`, índices `ix_...`, únicos `uq_...` e checagens `ck_...`): `fonte_dados`, `arquivo_dados`, `unidade_notificacao`, `semana_epidemiologica`, `registro_epidemiologico`, `serie_temporal`, `modelo_preditivo`, `metrica_modelo` e `log_processamento`. O esquema foi validado em PostgreSQL 16 (via container Docker), com 0 chaves estrangeiras órfãs e todas as tabelas e colunas comentadas; a camada de acesso é compatível com SQLite para os testes do backend. O diagrama de entidade-relacionamento está no Apêndice A (ver `../der_banco.png`).

### 4.5 Backend e API REST

O backend é construído em FastAPI, organizado em camadas (rotas, serviços, repositórios, modelos ORM e schemas), com acesso a dados via SQLAlchemy e `DATABASE_URL` lida de variável de ambiente. São 6 endpoints com contrato JSON `{sucesso, dados, mensagem}`: `/api/status`, `/api/dados` (RF001), `/api/series-temporais` (RF001), `/api/previsoes` (RF002), `/api/metricas` (RF004) e `/api/unidades-notificacao` (RF003). A validação de intervalo retorna 400/422 com mensagem clara, sem vazar stack trace. A tolerância a falhas é explícita: a indisponibilidade do modelo retorna 503 de forma isolada, sem derrubar os endpoints de dados históricos.

### 4.6 Modelo preditivo

O modelo principal é um Random Forest (scikit-learn) com engenharia de atributos temporais: defasagens de 1 a 4 semanas (lags), médias móveis de 3 e 5 semanas, e codificação de sazonalidade por seno e cosseno do ciclo de 52 semanas, mais o mês. A previsão de horizonte 6 é recursiva. O protocolo de avaliação é o walk-forward de origem expansiva (nunca aleatório). Os comparadores são o baseline sazonal-ingênuo, o SARIMA (statsmodels) e o Prophet, todos sob o mesmo protocolo. As métricas são MAE, RMSE, MAPE (restrito a semanas com real maior que zero), sMAPE e acerto direcional. A significância é avaliada por Diebold-Mariano, com a correção de Harvey, Leybourne e Newbold (1997), e por Wilcoxon. O modelo é serializado (`models/modelo_rf_v1.joblib`) e suas métricas são registradas no banco e servidas por `/api/metricas`.

### 4.7 Frontend e dashboard

O dashboard é construído em Next.js (App Router) com TypeScript e gráficos em Recharts, consumindo os seis endpoints por uma camada de serviços tipada. Atende ao RF001 (filtro por período, cards de indicadores e gráficos da série histórica) e ao RF002 (gráfico de comparação real versus previsto, com a previsão visualmente separada do dado real). A degradação é elegante: o 503 do preditor vira um estado específico, exibido apenas no bloco de previsão, enquanto histórico e cards seguem renderizando. A honestidade de dados é preservada: o filtro por unidade trata a pendência de NM_UN_INTE sem inventar unidades, e há ressalva de protótipo acadêmico no rodapé. Nesta fase, lint e build concluem sem erros; a integração ponta a ponta com dados reais depende de um banco populado.

### 4.8 Arquitetura, nuvem e segurança

Em resposta à crítica do TC1 sobre arquitetura superficial, os atributos de qualidade são amarrados às normas ISO/IEC 25010 (produto de software), 25012 (dados), 25059 (sistemas de IA) e 27002 (controles de segurança da informação). Os pontos tratados incluem:

- **Segurança e autenticação:** credenciais fora do código, lidas de variável de ambiente; `.env` ignorado pelo versionamento; autenticação de rotas administrativas (por exemplo, JWT) planejada para a fase de nuvem.
- **Logs:** registro estruturado (timestamp, nível, origem) e tabela `log_processamento` já ativa, apoiando analisabilidade e monitoramento.
- **Backup:** backup do banco (RDS) e dos artefatos (S3), com teste de restauração, planejado.
- **Versionamento de modelo:** versão ativa registrada em `modelo_preditivo`/`metrica_modelo`, suportando gestão de mudanças.
- **Custos e escalabilidade:** plano de implantação em AWS (EC2 para a API, RDS para o banco, S3 para artefatos) como fase futura, com camada de acesso portável entre PostgreSQL e SQLite para flexibilidade. O detalhamento está em `docs/arquitetura_descricao.md`, `docs/plano_nuvem.md` e `docs/plano_seguranca.md`.

### 4.9 Análise exploratória complementar: recorte intramunicipal por distrito (ponte CNES)

Esta subseção descreve o método da análise exploratória complementar, reposicionada como prova de conceito e separada do núcleo preditivo municipal.

**Método.** Para cada caso de SRAG da capital, o nome do hospital de internação (campo NM_UN_INTE do SRAG, texto livre) é normalizado (maiúsculas, remoção de acentos, expansão de abreviações) e casado contra o cadastro público de estabelecimentos CNES do município. O match é exato por nome em 94,6% dos 148 nomes distintos processados em 2024, complementado por match aproximado (rapidfuzz) e por um fallback por bairro. Do estabelecimento casado obtém-se a latitude e a longitude, submetidas a um join espacial point-in-polygon contra as camadas territoriais do GeoSampa (96 distritos e 32 subprefeituras, no sistema de coordenadas EPSG:31983), resolvendo distrito, subprefeitura e zona; o bairro vem direto do campo NO_BAIRRO do CNES. Todas as fontes são públicas e sem credencial.

**Enquadramento de proteção de dados (LGPD e ISO/IEC 25012, Confidencialidade).** O recorte geográfico vem exclusivamente do endereço público do hospital (CNES), nunca do paciente. A saída é sempre agregada por semana epidemiológica mais distrito-do-hospital, sem nenhuma linha que represente um indivíduo. Nenhum dado individual identificável é produzido. O atendimento ao atributo de Confidencialidade decorre justamente de o dado sensível de localização individual nunca entrar no pipeline.

**Procedência dos números (análise exploratória, fontes públicas).** Os valores reportados nesta subseção e na seção 5.3 provêm de uma investigação exploratória conduzida de forma deliberadamente isolada, apoiada apenas em fontes públicas: os microdados de SRAG do openDATASUS referentes a 2024, o cadastro público de estabelecimentos CNES e as camadas territoriais do GeoSampa obtidas via WFS, todas com extração datada de outubro de 2026. Os relatórios de saída dessa investigação estão versionados neste repositório, para rastreabilidade e auditoria, na pasta [`docs/tcc/ponte_cnes/`](ponte_cnes/README.md): o relatório de viabilidade ([`RELATORIO_VIABILIDADE_PONTE.md`](ponte_cnes/RELATORIO_VIABILIDADE_PONTE.md)), o relatório de cobertura ([`RELATORIO_COBERTURA.md`](ponte_cnes/RELATORIO_COBERTURA.md)) e a ficha de rastreabilidade das fontes ([`FICHA_RASTREABILIDADE_FONTES.md`](ponte_cnes/FICHA_RASTREABILIDADE_FONTES.md)). Os scripts reprodutíveis permanecem na área de investigação isolada, externa ao repositório. A reprodução a escala total, cobrindo todos os anos do período, é tratada como trabalho futuro, e a ponte permanece prova de conceito validada somente em 2024.

---

## 5 Resultados

### 5.1 Resultados do núcleo prático

Foram construídos e validados: o ETL (13.139 registros do município filtrados; série contínua de 832 semanas; 8 semanas recentes reservadas); o banco relacional (9 tabelas em 3FN, validadas em PostgreSQL 16, sem chaves estrangeiras órfãs e sem comentários faltantes); o backend/API REST (6 endpoints com contrato JSON padronizado, validação e tolerância a falhas); e o dashboard Next.js (RF001 e RF002, com lint e build validados). O conjunto de testes do backend soma 32 testes (15 do modelo, 12 da API e 5 do ETL).

### 5.2 Resultados do modelo preditivo (honestidade metodológica)

A Tabela 2 apresenta as métricas efetivamente obtidas sob validação walk-forward (origem expansiva, horizonte de 6 semanas).

**Tabela 2: Métricas comparativas dos modelos.**

| Modelo | MAE | RMSE | sMAPE (%) | Acerto direcional |
| ------ | --- | ---- | --------- | ----------------- |
| baseline (sazonal-ingênuo) | 8,28 | 22,86 | 47,33 | 0,512 |
| random_forest | 8,56 | 25,48 | 37,51 | 0,531 |
| sarima | 7,51 | 23,34 | 44,53 | 0,482 |
| prophet | 10,38 | 23,07 | 46,96 | 0,532 |

O teste de Diebold-Mariano do Random Forest frente a cada comparador resultou em: baseline com p igual a 0,512; SARIMA com p igual a 0,336; e Prophet com p igual a 0,542. Nenhuma diferença é estatisticamente significativa.

**Leitura honesta.** Nesta série curta e esparsa, o Random Forest não superou o baseline em MAE e RMSE, e o teste de Diebold-Mariano não indicou vantagem significativa frente a nenhum comparador. O SARIMA obteve o menor MAE (7,51). Conforme o posicionamento do projeto, o modelo não pode ser apresentado como comprovadamente superior: o artefato é entregue e integrado por completude do RF004, com desempenho reportado de forma transparente. O gráfico real versus previsto está no Apêndice B (ver `../grafico_real_x_previsto.png`).

### 5.3 Resultados da análise exploratória da ponte por distrito (2024)

A prova de conceito foi aplicada ao ano de 2024, que traz o campo NM_UN_INTE preenchido. Dos 18.574 casos notificados na capital, 90,0% foram resolvidos a um distrito (86,9% por ponto, via point-in-polygon, mais 3,1% por fallback de bairro); 10,0% não foram mapeados e foram tratados de forma fail-closed (não atribuídos). A Tabela 3 lista os distritos com mais casos no ano.

Convém distinguir os dois percentuais citados, pois têm denominadores diferentes. O match exato de 94,6% da seção 4.9 refere-se a NOMES DISTINTOS de unidade de internação (148 nomes distintos casados contra o CNES). Já os 90,0% aqui reportados referem-se à cobertura de CASOS resolvidos a um distrito, ponderada pelo volume de notificações de 2024. Em resumo, 94,6% mede acerto sobre nomes distintos de unidade, enquanto 90,0% mede a fração de casos efetivamente localizados; são métricas distintas e não devem ser somadas nem comparadas diretamente.

**Tabela 3: Distritos com mais casos resolvidos em 2024 (recorte por hospital notificante).**

| Distrito | Casos | % do total do ano |
| -------- | ----- | ----------------- |
| Bela Vista | 4.230 | 22,8% |
| Bom Retiro | 1.498 | 8,1% |
| Consolação | 1.206 | 6,5% |
| Vila Mariana | 979 | 5,3% |
| Morumbi | 916 | 4,9% |
| Vila Prudente | 877 | 4,7% |
| Jardim São Luís | 815 | 4,4% |
| Mooca | 566 | 3,0% |

**Limitação central (sem suavização).** O distrito atribuído é o do HOSPITAL, não o da RESIDÊNCIA do paciente. Hospitais de referência atraem casos de toda a cidade: o distrito de Bela Vista concentra 22,8% dos casos não por abrigar a maior parte dos doentes, mas por sediar grandes unidades de referência (por exemplo, o complexo HC-FMUSP). Portanto, a série por distrito deve ser lida como carga assistencial por distrito do hospital, e não como incidência por local de moradia.

**Aplicabilidade parcial.** O ano de 2013 não possui o campo NM_UN_INTE, resultando em cobertura zero; a ponte foi validada apenas em 2024. Trata-se, assim, de prova de conceito, com aplicabilidade a confirmar ano a ano, pois os primeiros anos do período (2009 a 2019) podem não trazer o campo.

**Enquadramento de utilidade (hipótese de aplicação futura).** Por medir carga assistencial por hospital, o recorte poderia, no futuro e após validação adicional, auxiliar o público a identificar unidades com menor volume de casos em determinado momento, evitando ambientes de maior risco de exposição. Esse uso é apresentado como hipótese de aplicação futura, não como recomendação oficial de saúde nem como impacto comprovado.

---

## 6 Considerações finais

O trabalho entregou um protótipo acadêmico completo em suas camadas essenciais (ETL, banco relacional, API REST, modelo preditivo e dashboard), com delimitação clara do problema, objetivos amarrados a métricas, revisão crítica de modelos, discussão da qualidade dos dados públicos e documentação de arquitetura, segurança e nuvem. Essas entregas respondem, ponto a ponto, às críticas recebidas na avaliação do TC1.

**Limitações declaradas.** A variável-alvo depende de uma proxy (PCR_FLUASU), por ausência dos campos de confirmação da Tabela 1 no arquivo consolidado; a série é curta e esparsa, com hiato em 2020 e 2021; há subnotificação e atraso de notificação (tratados com a reserva das 8 semanas recentes); o modelo não demonstrou superioridade estatística frente ao baseline; o campo NM_UN_INTE não é populado na base consolidada do núcleo prático; a nuvem não foi provisionada neste ambiente; e a ponte por distrito foi validada apenas em 2024.

**Trabalhos futuros.** Validar a ponte ano a ano e, quando aplicável, estendê-la ao período completo; evoluir o frontend com um mapa por distrito para a análise exploratória; implantar a solução em AWS (EC2, RDS e S3) com os controles de segurança planejados; reextrair os dados com os campos de confirmação da Tabela 1 para substituir a proxy; estabelecer retreinamento periódico do modelo (concept drift) e explicabilidade (importância de variáveis) no dashboard; e investigar, como hipótese, a aplicação de orientação ao público sobre carga assistencial por hospital, sempre condicionada a validação adicional e sem caráter de recomendação oficial.

---

## Referências

As referências seguem a ABNT NBR 6023 e sustentam cada decisão e técnica aplicada.

### Normas técnicas

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e documentação: referências: elaboração. Rio de Janeiro: ABNT, 2018.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6027**: informação e documentação: sumário: apresentação. Rio de Janeiro: ABNT, 2012.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6028**: informação e documentação: resumo, resenha e recensão: apresentação. Rio de Janeiro: ABNT, 2021.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10520**: informação e documentação: citações em documentos: apresentação. Rio de Janeiro: ABNT, 2023.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL COMMISSION. **ISO/IEC 25010:2023**: systems and software engineering: SQuaRE: product quality model. Geneva: ISO/IEC, 2023. Disponível em: [https://www.iso.org/standard/78176.html](https://www.iso.org/standard/78176.html). Acesso em: 30 set. 2026.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL COMMISSION. **ISO/IEC 25012:2008**: software engineering: SQuaRE: data quality model. Geneva: ISO/IEC, 2008. Disponível em: [https://www.iso.org/standard/35736.html](https://www.iso.org/standard/35736.html). Acesso em: 30 set. 2026.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL COMMISSION. **ISO/IEC 25059:2023**: SQuaRE: quality model for AI systems. Geneva: ISO/IEC, 2023. Disponível em: [https://www.iso.org/standard/80655.html](https://www.iso.org/standard/80655.html). Acesso em: 30 set. 2026.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION; INTERNATIONAL ELECTROTECHNICAL COMMISSION. **ISO/IEC 27002:2022**: information security, cybersecurity and privacy protection: information security controls. Geneva: ISO/IEC, 2022. Disponível em: [https://www.iso.org/standard/75652.html](https://www.iso.org/standard/75652.html). Acesso em: 30 set. 2026.

### Fontes de dados e legislação

BRASIL. Ministério da Saúde. **SIVEP-Gripe: dados de Síndrome Respiratória Aguda Grave (SRAG)**. Portal de Dados Abertos do SUS (openDataSUS). Disponível em: [https://opendatasus.saude.gov.br/](https://opendatasus.saude.gov.br/). Acesso em: 30 set. 2026.

BRASIL. Ministério da Saúde. **CNES: Cadastro Nacional de Estabelecimentos de Saúde**. DATASUS. Disponível em: [https://cnes.datasus.gov.br/](https://cnes.datasus.gov.br/). Acesso em: 1 out. 2026.

BRASIL. **Lei nº 13.709, de 14 de agosto de 2018**: Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília: Presidência da República, 2018.

PREFEITURA DO MUNICÍPIO DE SÃO PAULO. **GeoSampa: mapa digital da cidade de São Paulo (camadas distrito_municipal e subprefeitura, via WFS)**. São Paulo: PMSP. Disponível em: [https://geosampa.prefeitura.sp.gov.br/](https://geosampa.prefeitura.sp.gov.br/). Acesso em: 1 out. 2026.

### Literatura das técnicas empregadas

BREIMAN, Leo. Random Forests. **Machine Learning**, v. 45, n. 1, p. 5-32, 2001.

DIEBOLD, Francis X.; MARIANO, Roberto S. Comparing Predictive Accuracy. **Journal of Business & Economic Statistics**, v. 13, n. 3, p. 253-263, 1995.

HARVEY, David; LEYBOURNE, Stephen; NEWBOLD, Paul. Testing the equality of prediction mean squared errors. **International Journal of Forecasting**, v. 13, n. 2, p. 281-291, 1997.

HYNDMAN, Rob J.; ATHANASOPOULOS, George. **Forecasting: Principles and Practice**. 3. ed. Melbourne: OTexts, 2021. Disponível em: [https://otexts.com/fpp3/](https://otexts.com/fpp3/). Acesso em: 30 set. 2026.

HYNDMAN, Rob J.; KOEHLER, Anne B. Another look at measures of forecast accuracy. **International Journal of Forecasting**, v. 22, n. 4, p. 679-688, 2006.

TAYLOR, Sean J.; LETHAM, Benjamin. Forecasting at scale. **The American Statistician**, v. 72, n. 1, p. 37-45, 2018.

WILCOXON, Frank. Individual Comparisons by Ranking Methods. **Biometrics Bulletin**, v. 1, n. 6, p. 80-83, 1945.

WORLD HEALTH ORGANIZATION. **Influenza (seasonal)**. Geneva: WHO, 2021. Disponível em: [https://www.who.int/news-room/fact-sheets/detail/influenza-(seasonal)](https://www.who.int/news-room/fact-sheets/detail/influenza-(seasonal)). Acesso em: 30 set. 2026.

### Bibliotecas e ferramentas (parte aplicada)

TIANGOLO, Sebastián. **FastAPI documentation**. Disponível em: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/). Acesso em: 30 set. 2026.

VERCEL. **Next.js documentation**. Disponível em: [https://nextjs.org/docs](https://nextjs.org/docs). Acesso em: 30 set. 2026.

RECHARTS. **Recharts documentation**. Disponível em: [https://recharts.org](https://recharts.org). Acesso em: 30 set. 2026.

SCIKIT-LEARN DEVELOPERS. **RandomForestRegressor**. Disponível em: [https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html). Acesso em: 30 set. 2026.

STATSMODELS DEVELOPERS. **SARIMAX**. Disponível em: [https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html). Acesso em: 30 set. 2026.

META (FACEBOOK). **Prophet: forecasting at scale**. Disponível em: [https://facebook.github.io/prophet/](https://facebook.github.io/prophet/). Acesso em: 30 set. 2026.

THE PANDAS DEVELOPMENT TEAM. **pandas documentation**. Disponível em: [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/). Acesso em: 30 set. 2026.

HARRIS, C. R. et al. **NumPy documentation**. Disponível em: [https://numpy.org/doc/](https://numpy.org/doc/). Acesso em: 30 set. 2026.

JOBLIB DEVELOPERS. **joblib documentation**. Disponível em: [https://joblib.readthedocs.io/](https://joblib.readthedocs.io/). Acesso em: 30 set. 2026.

SQLALCHEMY DEVELOPERS. **SQLAlchemy 2.0 documentation**. Disponível em: [https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/). Acesso em: 30 set. 2026.

POSTGRESQL GLOBAL DEVELOPMENT GROUP. **PostgreSQL documentation**. Disponível em: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/). Acesso em: 30 set. 2026.

GEOPANDAS DEVELOPERS. **GeoPandas documentation**. Disponível em: [https://geopandas.org/](https://geopandas.org/). Acesso em: 1 out. 2026.

SHAPELY DEVELOPERS. **Shapely documentation**. Disponível em: [https://shapely.readthedocs.io/](https://shapely.readthedocs.io/). Acesso em: 1 out. 2026.

RAPIDFUZZ DEVELOPERS. **RapidFuzz documentation**. Disponível em: [https://rapidfuzz.github.io/RapidFuzz/](https://rapidfuzz.github.io/RapidFuzz/). Acesso em: 1 out. 2026.

### Documentos internos do projeto (fonte de decisões)

MANUAL INTERNO DE DESENVOLVIMENTO DO TCC (v2). `Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx`.

TCC: C D H M (TC2). `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx`.

ANEXO DE QUALIDADE ISO/IEC 25000 v4. `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`.

MANUAL PADRÃO DE DOCUMENTAÇÃO DE BANCOS DE DADOS. `Documentos_Para_Desenv_TCC/Manual_Padrao_Documentacao_Bancos_de_Dados.docx`.

NORMAS CNPq SOBRE USO DE IA. `Documentos_Para_Desenv_TCC/Normas CNPQ Uso de IA.pdf`.

---

## Apêndices e anexos

- **Apêndice A: Diagrama de entidade-relacionamento (DER) do banco.** Figura em `../der_banco.png`.
- **Apêndice B: Gráfico real versus previsto do modelo preditivo.** Figura em `../grafico_real_x_previsto.png`.
- **Apêndice C: Matriz de rastreabilidade (RF para entregável para validação).** Consolidada na seção 6.6 de `docs/documentacao_projeto.md`, que amarra RF001 a RF004 aos arquivos construídos e às evidências de teste.

---

## Declaração de uso de inteligência artificial

Em conformidade com as Normas CNPq sobre uso de IA, registra-se de forma transparente que ferramentas de inteligência artificial foram utilizadas como apoio ao desenvolvimento do projeto e à elaboração deste material de apoio (por exemplo, apoio à redação, à organização de documentação e à revisão de texto). As decisões metodológicas, a definição de escopo, a interpretação dos resultados e a validação final são de responsabilidade dos autores. Nenhum resultado numérico foi gerado por IA sem respaldo nos artefatos efetivamente produzidos no núcleo prático (métricas, tabelas, gráficos e relatórios de cobertura).
