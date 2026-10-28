# Relatorio de validacao da metodologia preditiva em uma segunda serie (Dengue / Sao Paulo)

> **ENQUADRAMENTO (leia primeiro).** Este documento descreve um **EXPERIMENTO DE
> VALIDACAO DA METODOLOGIA** preditiva do TCC, aplicado a uma **segunda serie
> temporal (Dengue, municipio de Sao Paulo)**, de forma **ISOLADA e
> NAO-INTEGRADA** ao repositorio oficial. **A Dengue NAO faz parte do objeto
> oficial do TCC**, que permanece **Influenza A / municipio de Sao Paulo**. O
> unico proposito aqui e verificar, com honestidade, se o mesmo pipeline supera o
> baseline (e com que significancia) quando a serie e mais densa. Trata-se de um
> **prototipo academico de verificacao de robustez metodologica**, sem qualquer
> promessa de impacto em saude publica e sem reaproveitamento de modelo, banco ou
> API do projeto oficial.

## Por que a Dengue (e nao a COVID-19)

A COVID-19 foi descartada porque e recente e o ano de explosao da pandemia teve
notificacao muito bagunçada e sem documentacao correta, o que contaminaria a
comparacao. A Dengue foi escolhida por ser uma doenca com serie longa, publica,
bem documentada e muito mais densa que a Influenza no mesmo municipio, servindo
como um teste mais justo da metodologia.

---

## (a) Disponibilidade, recorte e granularidade da serie

- **Fonte:** InfoDengue (FGV / Fundacao Oswaldo Cruz - Fiocruz), API publica
  `alertcity`.
- **Endpoint exato:**
  `https://info.dengue.mat.br/api/alertcity?geocode=3550308&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2010&ey_end=2024`
- **Data da extracao (UTC):** 2026-10-28T00:56:47+00:00.
- **Recorte geografico:** municipio de Sao Paulo (codigo IBGE 3550308) - o
  **mesmo** municipio do objeto oficial do TCC.
- **Granularidade:** semana epidemiologica (campo `SE`, formato AAAASS).
- **Periodo:** 2010 a 2024.
- **Alvo (`CASOS_PROXY`):** coluna `casos` da API (casos notificados/confirmados
  de dengue por semana), espelhando o papel de `CASOS_PROXY` na serie oficial de
  Influenza.
- **Disponibilidade:** a serie foi obtida de forma reprodutivel e idempotente
  pelo `scripts/01_download_dengue.py` (ver `dados_brutos/FICHA_RASTREABILIDADE.md`).

## (b) Volume e densidade vs Influenza

| Caracteristica | Dengue (este experimento) | Influenza A (objeto oficial do TCC) |
| --- | --- | --- |
| Semanas totais | **782** | **832** |
| Semanas com zero casos | **0** | esparsa: **242** semanas ignoradas no MAPE |
| Amplitude de `CASOS_PROXY` | min **38** / max **85389** / media **2188.86** | proxy PCR escasso, baseline MAE **8.2846** |

Leitura: as duas series tem comprimento parecido (782 vs 832 semanas), mas a
**densidade e radicalmente diferente**. A serie de Dengue **nao tem nenhuma
semana de zero casos** e opera em uma escala de milhares de casos por semana,
enquanto a serie de Influenza e esparsa (muitos zeros, 242 semanas descartadas do
MAPE classico) e de baixa magnitude. Ou seja, a Dengue e exatamente o cenario
"serie densa" que este experimento quer testar.

> **Observacao importante sobre escala.** Como a Dengue opera em milhares de
> casos e a Influenza em dezenas, os valores absolutos de MAE/RMSE **nao sao
> comparaveis diretamente** entre as duas doencas. A comparacao valida e
> **relativa dentro de cada serie** (cada modelo frente ao seu proprio baseline)
> e via metricas adimensionais (sMAPE, acerto direcional) e testes de
> significancia.

## (c) Tabela de metricas dos 4 modelos (walk-forward)

Numeros **reais** reproduzidos de `saida/metricas_dengue.csv` (nada digitado a
mao). Protocolo: validacao cronologica walk-forward, origem expansiva, horizonte
de 6 semanas, janela minima de 60 semanas; 121 blocos, 722 pontos de teste.

| modelo | mae | rmse | mape_semanas_positivas | smape | acerto_direcional | semanas_ignoradas_mape |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 2147.4285 | 9997.5144 | 109.89 | 35.4869 | 0.6519 | 0 |
| random_forest | 1388.2715 | 6467.8756 | 46.9795 | 17.8855 | 0.6130 | 0 |
| sarima | 1310.7079 | 7092.0996 | 43.7522 | 22.2946 | 0.5548 | 0 |
| prophet | 2401.6853 | 9301.6517 | 179.9007 | 53.5398 | 0.4840 | 0 |

Destaques:

- O **Random Forest tem MAE menor que o baseline** (1388.27 vs 2147.43), reduz o
  RMSE (6467.88 vs 9997.51) e corta o sMAPE pela metade (17.89% vs 35.49%).
- O **SARIMA tem o menor MAE da tabela** (1310.71) e o menor MAPE classico
  (43.75%), ficando a frente do proprio RF em MAE, embora com RMSE e sMAPE
  piores (SARIMA 22.29% vs RF 17.89%).
- O **Prophet foi o pior** nesta serie (MAE 2401.69, abaixo ate do baseline).
- O **acerto direcional** do baseline (0.6519) ficou **acima** do RF (0.6130) e
  do SARIMA (0.5548): a media sazonal acerta bem a direcao subida/descida, ainda
  que erre mais a magnitude.

## (d) Testes de significancia (Diebold-Mariano e Wilcoxon)

RF e o modelo 1 (erros = real - previsto). DM < 0 favorece o RF. Valores reais de
`saida/metricas_dengue.csv`:

| comparador (vs RF) | DM* | DM p-valor | DM significativo | Wilcoxon p-valor | Wilcoxon significativo |
| --- | --- | --- | --- | --- | --- |
| baseline | -0.9262 | 0.3547 | nao | 0.0 | sim |
| sarima | -0.3826 | 0.7022 | nao | 0.0169 | sim |
| prophet | -0.9146 | 0.3607 | nao | 0.0 | sim |

Leitura dos testes:

- **Diebold-Mariano (teste principal, perda quadratica):** em todos os pares o
  DM* e negativo (aponta o RF como mais acurado em erro quadratico), mas **em
  nenhum caso a diferenca e estatisticamente significativa** (todos os p-valores
  acima de 0.05: 0.3547 vs baseline, 0.7022 vs SARIMA, 0.3607 vs Prophet). O DM e
  dominado por poucos picos epidemicos gigantescos, o que infla a variancia do
  diferencial de perda e derruba o poder do teste.
- **Wilcoxon (nao parametrico, erros absolutos pareados):** aqui a diferenca e
  **significativa** frente aos tres comparadores (p = 0.0 vs baseline e Prophet;
  p = 0.0169 vs SARIMA). Ou seja, na mediana dos erros absolutos o RF e
  consistentemente melhor que baseline e Prophet; frente ao SARIMA, o Wilcoxon
  apenas indica que a diferenca do erro mediano absoluto e estatisticamente
  significativa, **nao** que o RF seja superior ao SARIMA de forma geral - na
  verdade o **SARIMA tem o MAE medio menor** (1310.71 vs 1388.27), pois poucos
  erros grandes puxam a media do RF para cima. O Wilcoxon, por operar sobre a
  mediana dos erros absolutos, capta o ganho do RF na massa de erros tipicos, mas
  nao contradiz o fato de o SARIMA vencer em MAE medio.

## (e) Leitura honesta: a metodologia se valida nesta serie?

Veredito direto e sem maquiagem:

- **Em magnitude de erro, o RF supera o baseline** nesta serie densa (MAE, RMSE e
  sMAPE todos melhores), e o **Wilcoxon confirma essa superioridade com
  significancia** (p = 0.0). Esse e um resultado **mais forte** do que o obtido na
  Influenza.
- **Porem, o teste principal (Diebold-Mariano) NAO acusa significancia** (p =
  0.3547 vs baseline). Como o DM e o teste eleito pelo Manual Interno como
  principal, a leitura rigorosa e: **a metodologia melhora o erro medio, mas a
  superioridade nao e confirmada pelo teste principal nesta serie**. A divergencia
  DM x Wilcoxon e informativa: ela mostra que o ganho do RF esta na massa de
  erros tipicos (capturada pelo Wilcoxon), e nao nos poucos picos epidemicos
  extremos (que dominam a perda quadratica do DM).
- **O melhor MAE da tabela e do SARIMA, nao do RF.** Isso reforca a honestidade:
  o RF nao e o campeao absoluto; um modelo estatistico classico de serie temporal
  foi competitivo ou superior em MAE/MAPE.

O que isso diz sobre a metodologia: o **pipeline e solido e reaplicavel** (mesmos
modulos, mesmos parametros, mesmo protocolo walk-forward rodaram sem adaptacao em
uma serie completamente diferente) e, numa serie densa, o RF **de fato reduz o
erro** frente ao baseline de forma detectavel por Wilcoxon. Mas a serie densa
**nao garante automaticamente significancia no teste principal**, porque a
dinamica da Dengue e dominada por surtos explosivos que tornam a comparacao de
perda quadratica muito ruidosa. A conclusao metodologica e **parcial e honesta**:
a abordagem funciona e melhora o erro, sem que se possa afirmar superioridade
estatistica forte (DM) sobre o baseline.

## (f) Comparacao direta com a Influenza (serie densa ajuda?)

Numeros oficiais da Influenza A (objeto do TCC), para contraste:

| metrica | Influenza A (oficial) | Dengue (este experimento) |
| --- | --- | --- |
| Semanas totais | 832 | 782 |
| Semanas ignoradas no MAPE | 242 | 0 |
| baseline MAE | 8.2846 | 2147.4285 |
| random_forest MAE | 8.5628 | 1388.2715 |
| sarima MAE | 7.5123 | 1310.7079 |
| prophet MAE | 10.3754 | 2401.6853 |
| DM RF vs baseline (p-valor) | 0.5117 (nao signif.) | 0.3547 (nao signif.) |

Leitura comparativa:

- **Na Influenza, o RF NAO superou o baseline** (MAE 8.5628 > 8.2846) e o DM foi
  nao significativo (p = 0.5117). **Na Dengue, o RF superou o baseline em MAE**
  (1388.27 < 2147.43) e, pelo Wilcoxon, com significancia. Portanto, **a serie
  mais densa melhorou o desempenho relativo do RF** - exatamente a hipotese que o
  experimento queria testar.
- **Contudo, o teste principal (DM) continuou nao significativo em ambas** (p =
  0.5117 na Influenza, p = 0.3547 na Dengue). A densidade ajudou a reduzir o erro
  e a inverter o sinal da vantagem do RF, mas **nao foi suficiente para cravar
  significancia no DM** frente ao baseline.
- Em ambas as series, o **SARIMA teve o menor MAE**, reforcando que modelos
  classicos de serie temporal sao competidores fortes nesse tipo de dado.

**Conclusao do experimento:** a metodologia e robusta e portavel, e uma serie
mais densa melhora o desempenho do Random Forest (que passa a vencer o baseline em
erro medio, confirmado por Wilcoxon). Mesmo assim, a superioridade **nao atinge
significancia no teste principal (Diebold-Mariano)**, e o SARIMA segue como o
menor MAE. O achado e **util e honesto** para apresentar a banca: valida o
pipeline e mostra o efeito da densidade dos dados, sem exagerar as conclusoes.

---

## Artefatos gerados (caminhos exatos)

Todos sob `/projects/sandbox/_exploracao_validacao_dengue/`:

- Serie semanal tratada: `saida/serie_semanal_dengue.csv`
- CSV bruto da API: `dados_brutos/dengue_sp_infodengue_2010_2024.csv`
- Ficha de rastreabilidade: `dados_brutos/FICHA_RASTREABILIDADE.md`
- Script de download/preparacao: `scripts/01_download_dengue.py`
- Script do pipeline (este experimento): `scripts/02_executar_pipeline_dengue.py`
- Modulos do pipeline (copia fiel, so imports ajustados): `pipeline_ref/`
- Tabela de metricas (CSV): `saida/metricas_dengue.csv`
- Tabela de metricas (Markdown): `saida/metricas_dengue.md`
- Grafico real x previsto: `saida/grafico_real_x_previsto_dengue.png`
- Este relatorio: `RELATORIO_VALIDACAO_DENGUE.md`

## Reproducao

```
cd /projects/sandbox/_exploracao_validacao_dengue
.venv/bin/python scripts/01_download_dengue.py        # (re)gera a serie
.venv/bin/python scripts/02_executar_pipeline_dengue.py  # metricas, testes e grafico
```

## Isolamento (requisito inegociavel)

Nenhum arquivo do repositorio oficial (`_repo_ref/`) ou de qualquer outro repo do
workspace foi modificado, criado ou removido. Nenhum `git add`/`commit` foi feito.
O `git status --porcelain` em `_repo_ref/` permaneceu vazio apos a execucao. Todo
artefato vive exclusivamente sob `/projects/sandbox/_exploracao_validacao_dengue/`.
Prophet esteve **disponivel** (prophet 1.5.0), portanto os 4 comparadores foram
avaliados.
