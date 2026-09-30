# Relatorio de Qualidade de Dados

Modulo de ETL (RF003) do TCC "Analise preditiva de Influenza A no municipio de
Sao Paulo utilizando IA com dados do SIVEP-Gripe". Este relatorio documenta com
honestidade academica as limitacoes da base real e amarra cada ponto as
caracteristicas de qualidade de dados da norma **ISO/IEC 25012** (modelo de
qualidade de dados da familia SQuaRE / ISO/IEC 25000), conforme o
**Anexo de Qualidade ISO/IEC 25000 v4** do projeto
(`Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`).

Protótipo academico - nao e ferramenta oficial de vigilancia epidemiologica.

## 1. Contexto da base

- Fonte: SIVEP-Gripe / SINAN (DATASUS), dados publicos de SRAG.
- Recorte: municipio de Sao Paulo capital (CO_MUN_RES = 355030), 13.139 de 48.775
  registros.
- Periodo: 2009-2019 e 2022-2026 (anos 2020-2021 ausentes na fonte consolidada).

## 2. Limitacao critica: campos de confirmacao laboratorial ausentes

O CSV consolidado **NAO contem** os campos de confirmacao laboratorial previstos
na Tabela 1 do TC2: `CLASSI_FIN`, `PCR_RESUL`, `POS_PCRFLU`, `TP_FLU_PCR`,
`POS_AN_FLU`, `TP_FLU_AN`. Estao disponiveis apenas:

- `PCR_FLUASU`: subtipo de Influenza A por PCR (6 categorias antigas);
- `FLUASU_OUT`: subtipo em texto livre (13.006 ausentes em SP).

### Regra de proxy adotada

Na ausencia dos campos de confirmacao, adotou-se a **regra de proxy**: todo
registro com `PCR_FLUASU` **preenchido (nao vazio)** e contado como
**caso-proxy de Influenza A** (`CASO_PROXY_INFLUENZA_A = 1`). Os campos ausentes
**nao foram fabricados**.

Distribuicao real de `PCR_FLUASU` no municipio de Sao Paulo:

| Categoria | Registros |
|-----------|-----------|
| `<vazio>` | 5.732 |
| `1` | 3.505 |
| `3` | 2.073 |
| `4` | 790 |
| `2` | 736 |
| `5` | 160 |
| `6` | 143 |
| **Total preenchido (proxy)** | **7.407** |

Para referencia, a distribuicao global (48.775 registros) e: vazio=19.400,
`1`=14.972, `3`=7.311, `2`=4.144, `4`=1.726, `6`=720, `5`=502.

**Amarracao ISO/IEC 25012 - Exatidao e Consistencia:** a proxy introduz uma
aproximacao entre o dado disponivel (subtipo por PCR) e o conceito desejado
(confirmacao de Influenza A), afetando a **Exatidao** (o valor pode nao
corresponder exatamente ao fenomeno real de confirmacao) e a **Consistencia**
(o criterio de confirmacao difere do padrao da Tabela 1 do TC2). A limitacao e
assumida explicitamente e a variavel-alvo do projeto e o caso-proxy.

## 3. Descompasso de granularidade: NM_UN_INTE ausente

O TC2 adota `NM_UN_INTE` (unidade de notificacao) como granularidade de consulta.
Esse campo **nao existe** no CSV consolidado. Assim, **a modelagem preditiva e
sempre MUNICIPAL** (contagem semanal de casos-proxy no municipio de Sao Paulo).
Nao foram criadas estruturas de bairro/regiao. Em modulos posteriores, a tabela
de unidade de notificacao podera existir apenas como estrutura, registrando que a
fonte atual nao popula o campo (pendencia documentada).

**Amarracao ISO/IEC 25012 - Completude:** a ausencia de `NM_UN_INTE` reduz a
**Completude** da base em relacao ao escopo originalmente previsto, restringindo a
granularidade analitica ao nivel municipal.

## 4. Subnotificacao

Dados de SRAG do SIVEP-Gripe estao sujeitos a subnotificacao: nem todos os casos
reais chegam ao sistema. As contagens representam casos notificados, nao a
incidencia real.

**Amarracao ISO/IEC 25012 - Completude:** a subnotificacao e uma incompletude
sistemica da fonte que deve ser considerada na interpretacao dos resultados.

## 5. Atraso de notificacao e reserva das 8 semanas recentes

Registros das semanas epidemiologicas mais recentes tendem a estar incompletos
(o caso ja ocorreu, mas a notificacao ainda nao foi consolidada). Para evitar
vies de treino com semanas ainda "em maturacao", as **8 semanas epidemiologicas
mais recentes** da serie sao marcadas como reservadas
(`RESERVADA_ATRASO_NOTIFICACAO = True`, `USAR_NO_TREINO = False`) e mantidas
apenas para consulta - regra do Manual Interno.

**Amarracao ISO/IEC 25012 - Completude e Atualidade (Currentness):** as semanas
recentes ainda nao atingiram completude; reserva-las preserva a qualidade do
conjunto de treino.

## 6. Sazonalidade

A Influenza A apresenta forte sazonalidade (picos tipicos no outono/inverno do
hemisferio sul). A serie temporal semanal preserva a granularidade necessaria para
capturar esse padrao na modelagem (baseline, SARIMA e, opcionalmente, Prophet).

**Amarracao ISO/IEC 25012 - Consistencia:** a agregacao semanal continua mantem a
consistencia temporal necessaria para a analise de sazonalidade.

## 7. Hiato 2020-2021 e continuidade da serie

Os anos 2020 e 2021 **nao constam** na fonte consolidada. A serie continua e
construida **somente sobre os anos presentes** (2009-2019 e 2022-2026); as semanas
sem casos nesses anos recebem contagem zero, mas os anos ausentes **nao** sao
preenchidos com zeros artificiais (isso confundiria "ausencia de dado" com
"ausencia de casos").

**Amarracao ISO/IEC 25012 - Completude e Exatidao:** preencher 2020-2021 com zeros
violaria a Exatidao; a decisao preserva a distincao entre dado ausente e valor zero.

## 8. Duplicidades e valores ausentes

- **Linhas identicas:** foram detectadas **361** linhas exatamente iguais em todas
  as colunas originais no recorte de SP. Como a base nao possui identificador unico
  de notificacao e o Manual Interno veda a exclusao de dados sem justificativa,
  esses registros **foram mantidos** (podem representar notificacoes distintas com
  os mesmos atributos). A decisao fica registrada em log de processamento. O ETL
  **nao introduz** duplicidades: a base tratada preserva exatamente os 13.139
  registros do municipio.
- **Valores ausentes (SP capital):** `CS_RACA`=261, `CS_ZONA`=7.319,
  `PCR_FLUASU`=5.732 (base da proxy), `FLUASU_OUT`=13.006. Os ausentes sao
  quantificados e registrados em log; nenhum registro e descartado por ausencia.

**Amarracao ISO/IEC 25012 - Completude e Consistencia.**

## 9. Prophet (nota de ambiente)

O pacote **Prophet** foi instalado com sucesso no ambiente (`prophet==1.4.0`) e
**permanece disponivel** como comparador opcional. Baseline e SARIMA seguem como
comparadores minimos obrigatorios (modulos posteriores). Caso, em outro ambiente,
a instalacao do Prophet falhe, ele deve ser removido do `pyproject.toml` e mantido
apenas como opcional documentado, sem prejuizo do baseline + SARIMA.

## 10. Referencias

- **ISO/IEC 25012** - Data quality model (familia ISO/IEC 25000 / SQuaRE):
  caracteristicas Exatidao, Completude, Consistencia e Atualidade.
- Anexo de Qualidade do projeto:
  `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx`.
- Manual Interno de Desenvolvimento:
  `Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx`.
- Definicao Conceitual:
  `Documentos_Para_Desenv_TCC/TCC_DefinicaoConceitual_v12 (1).docx`.
- Dicionario de dados do SIVEP-Gripe:
  `Documentos_Para_Desenv_TCC/DIC_DADOS_Influenza_v6 2023.pdf` e versoes anteriores.
