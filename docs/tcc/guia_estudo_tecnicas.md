# Guia de estudo das tecnicas do projeto para defesa de banca

> **Natureza deste documento.** Este e um material de estudo e apoio, escrito para que o aluno consiga explicar e defender, com as proprias palavras, cada tecnica e decisao tecnica empregada no nucleo pratico do projeto. Ele NAO substitui o TC2 do grupo (`Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx`), nem o documento de TCC consolidado (`docs/tcc/TCC_Influenza_A_SP_v1.md`), nem a documentacao tecnica (`docs/documentacao_modelo.md`). E um roteiro de estudo complementar.
>
> **Posicionamento (honestidade metodologica).** O que foi construido e um **prototipo academico** de previsao de casos-proxy de Influenza A no municipio de Sao Paulo. Os resultados sao relatados de forma transparente: o Random Forest NAO superou o baseline em MAE e RMSE, e o teste de Diebold-Mariano NAO indicou vantagem estatisticamente significativa em nenhum comparador. O modelo e entregue por completude do escopo, com desempenho reportado com honestidade, e NAO como comprovadamente superior. Toda afirmacao de resultado neste guia tem respaldo em `docs/metricas_modelos.md`.
>
> **Como usar este guia.** Para cada tecnica de modelagem voce encontra seis blocos fixos: (1) o que e, em linguagem acessivel; (2) a fonte original com link; (3) onde no projeto foi aplicada (arquivo e funcao exatos); (4) como foi aplicada; (5) o numero ou resultado real obtido; (6) como interpretar. Estude cada tecnica ate conseguir reproduzir o raciocinio sem olhar o texto.

---

## Indice

1. [Random Forest (modelo preditivo principal)](#1-random-forest-modelo-preditivo-principal)
2. [Engenharia de atributos temporais](#2-engenharia-de-atributos-temporais)
3. [Validacao walk-forward (origem expansiva)](#3-validacao-walk-forward-origem-expansiva)
4. [Baseline sazonal-ingenuo](#4-baseline-sazonal-ingenuo)
5. [SARIMA](#5-sarima)
6. [Prophet](#6-prophet)
7. [Metricas de avaliacao (MAE, RMSE, MAPE, sMAPE, acerto direcional)](#7-metricas-de-avaliacao-mae-rmse-mape-smape-acerto-direcional)
8. [Teste de Diebold-Mariano](#8-teste-de-diebold-mariano)
9. [Teste de Wilcoxon dos postos com sinais](#9-teste-de-wilcoxon-dos-postos-com-sinais)
10. [Stack de tecnologias (entradas resumidas)](#10-stack-de-tecnologias-entradas-resumidas)
11. [Tabela-resumo e pontos de defesa de banca](#11-tabela-resumo-e-pontos-de-defesa-de-banca)

---

## 1. Random Forest (modelo preditivo principal)

**O que e.** O Random Forest (floresta aleatoria) e um metodo de aprendizado de maquina do tipo *ensemble*: ele treina varias arvores de decisao, cada uma sobre uma amostra diferente dos dados (tecnica de *bagging*, ou agregacao por reamostragem com reposicao) e usando um subconjunto aleatorio dos atributos em cada divisao. A previsao final, no caso de regressao, e a media das previsoes de todas as arvores. Essa combinacao reduz a variancia de uma arvore isolada e deixa o modelo mais estavel. Uma limitacao importante para defender na banca: por ser baseado em medias de valores ja vistos, o Random Forest NAO extrapola tendencia para fora da faixa de valores observada no treino. Isso e especialmente relevante numa serie epidemiologica com picos: se o pico futuro for maior do que qualquer valor historico, o modelo tende a subestima-lo.

**Fonte original.** Breiman, L. (2001). "Random Forests". *Machine Learning*, 45(1), 5-32. Disponivel em [link.springer.com](https://link.springer.com/article/10.1023/A:1010933404324). Implementacao usada: [scikit-learn RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

**Onde no projeto.** Em `backend/app/model/preditor.py`, a classe `PreditorRandomForest` e o metodo `PreditorRandomForest.prever_series` (previsao recursiva multi-passo). O treino e a avaliacao do bloco ficam em `backend/app/model/walk_forward.py`, na funcao `preditor_random_forest`, que instancia o `RandomForestRegressor` do `sklearn.ensemble`.

**Como foi aplicada.** No treino, a serie semanal e convertida numa matriz supervisionada de atributos pela engenharia de atributos (secao 2) e o `RandomForestRegressor` e ajustado sobre esses pares. Na previsao de 6 semanas, o metodo `prever_series` opera de forma recursiva: preve a proxima semana, reinsere essa previsao no historico, recalcula os atributos e preve a semana seguinte, repetindo ate completar o horizonte. As previsoes sao limitadas a valores nao negativos (`max(estimativa, 0.0)`), porque contagem de casos nao pode ser negativa.

**Numero real.** MAE 8,56, RMSE 25,48, sMAPE 37,51%, acerto direcional 0,531.

**Como interpretar.** O Random Forest NAO superou o baseline em MAE (8,56 contra 8,28) nem em RMSE (25,48 contra 22,86). Ele teve o melhor sMAPE entre os modelos (menor erro percentual simetrico), mas isso nao basta para afirmar superioridade: o erro absoluto, que e a metrica central aqui, foi maior que o do baseline. A leitura honesta e que, nesta serie curta e esparsa, o modelo complexo nao trouxe ganho comprovado sobre a regua simples.

---

## 2. Engenharia de atributos temporais

**O que e.** Modelos como o Random Forest nao entendem "tempo" sozinhos: eles precisam receber o tempo transformado em colunas (atributos). Engenharia de atributos temporais e justamente criar essas colunas a partir da propria serie. As usadas aqui sao: *lags* (defasagens) de 1 a 4 semanas (o valor de 1, 2, 3 e 4 semanas atras), medias moveis de 3 e 5 semanas (a tendencia recente) e indicadores de sazonalidade derivados da semana epidemiologica. O cuidado central e nao usar informacao do futuro: cada linha so olha para valores passados, o que evita o vazamento de dados (quando o modelo "espia" a resposta e parece bom no teste, mas falha na pratica).

**Fonte original.** Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*. Disponivel em [otexts.com/fpp3](https://otexts.com/fpp3/).

**Onde no projeto.** Em `backend/app/model/features.py`: a configuracao `ConfigAtributos` (lags `(1, 2, 3, 4)`, janelas de media movel `(3, 5)`, sazonalidade ativada), a funcao `gerar_atributos_serie` (monta a matriz de treino), a funcao `gerar_atributos_proxima_semana` (monta o vetor de uma unica semana futura na previsao recursiva) e a funcao auxiliar `_atributos_sazonais`.

**Como foi aplicada.** Para cada semana-alvo com historico suficiente, o codigo monta uma linha com: os valores defasados (`valores[t - k]` para cada lag), as medias moveis calculadas apenas sobre o trecho anterior a semana-alvo (`valores[t - janela : t]`) e os atributos sazonais. A sazonalidade usa seno e cosseno do ciclo anual: `angulo = 2 * pi * (numero_semana / 52)`, e um "mes aproximado" (`_mes_aproximado`, que divide o numero da semana por 4,34524). O seno e o cosseno juntos capturam a posicao ciclica no ano de forma continua, sem o salto artificial entre a semana 52 e a semana 1. O mesmo gerador e usado no treino e na previsao, garantindo que o formato dos atributos seja identico nos dois momentos.

**Numero real.** Nao ha metrica propria desta etapa; ela alimenta o Random Forest da secao 1 (MAE 8,56).

**Como interpretar.** O ponto forte a defender e metodologico: ao usar apenas informacao passada em cada linha, o projeto evita vazamento de futuro, que e um erro classico que inflaria artificialmente o desempenho. A sazonalidade seno/cosseno e a forma correta de representar um ciclo (a semana 52 fica "ao lado" da semana 1).

---

## 3. Validacao walk-forward (origem expansiva)

**O que e.** Em series temporais nunca se pode embaralhar os dados ao dividir treino e teste, porque isso permitiria treinar com o futuro e testar no passado, o que nao existe na realidade. A validacao walk-forward (ou validacao cronologica) respeita a ordem do tempo: o teste e sempre posterior ao treino. Na variante de origem expansiva (*expanding window*), a cada passo o modelo e treinado com todo o historico disponivel ate a origem, preve o proximo bloco de semanas, e entao a origem avanca e o processo se repete. Assim o treino vai crescendo e o teste caminha sempre para frente.

**Fonte original.** Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*, capitulo de validacao cruzada em series temporais. Disponivel em [otexts.com/fpp3/tscv.html](https://otexts.com/fpp3/tscv.html).

**Onde no projeto.** Em `backend/app/model/walk_forward.py`, a funcao `avaliar_walk_forward`.

**Como foi aplicada.** A funcao comeca com uma janela minima de historico (`janela_minima`) e avanca em blocos de tamanho `horizonte` (6 semanas, o horizonte preditivo do projeto). Em cada passo, treina o preditor sobre o historico ate a origem, preve o bloco seguinte e concatena os pares (real, previsto) de todos os blocos. Esses pares acumulados sao depois usados para calcular as metricas (secao 7) e os testes de significancia (secoes 8 e 9). Todos os modelos (baseline, Random Forest, SARIMA e Prophet) sao avaliados sob exatamente o mesmo protocolo, o que torna a comparacao justa. Ha ainda uma protecao: se um preditor falhar num bloco, o codigo cai no ultimo valor observado como previsao, para a avaliacao nao quebrar.

**Numero real.** Protocolo que produz todos os numeros da tabela da secao 11 (horizonte de 6 semanas, origem expansiva).

**Como interpretar.** O argumento de defesa e que a comparacao entre modelos e honesta porque todos passaram pelo mesmo esquema cronologico, sem vazamento. O walk-forward e mais realista do que uma unica divisao treino/teste, porque simula o uso do modelo repetidas vezes ao longo do tempo.

---

## 4. Baseline sazonal-ingenuo

**O que e.** Um baseline (modelo de referencia) e um modelo propositalmente simples que serve de regua: so vale a pena usar um modelo complexo se ele vencer o baseline. Aqui o baseline e sazonal-ingenuo: para prever uma semana epidemiologica, usa a media historica dos casos daquela mesma semana nos anos anteriores. Quando a semana-alvo nunca apareceu no historico, cai para o ultimo valor observado (persistencia ingenua, ou *naive*).

**Fonte original.** Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*, capitulo de metodos simples de referencia (*simple forecasting methods*). Disponivel em [otexts.com/fpp3](https://otexts.com/fpp3/).

**Onde no projeto.** Em `backend/app/model/walk_forward.py`, a funcao `preditor_baseline_sazonal`.

**Como foi aplicada.** O codigo agrupa o historico por numero de semana epidemiologica, calcula a media dos casos de cada semana e usa essa media como previsao. Se a semana-alvo nao tiver amostra no historico, usa o ultimo valor observado como *fallback*.

**Numero real.** MAE 8,28, RMSE 22,86, sMAPE 47,33%, acerto direcional 0,5125.

**Como interpretar.** Ponto de defesa importante: o baseline teve MAE MENOR (8,28) do que o Random Forest (8,56) e tambem menor RMSE. Ou seja, a regua simples empatou ou superou o modelo complexo em erro absoluto. Isso nao e um defeito do trabalho: e um resultado legitimo e comum em series curtas e esparsas, e demonstra rigor em ter incluido o baseline. Sem ele, nao haveria como saber se o modelo complexo agregou valor.

---

## 5. SARIMA

**O que e.** SARIMA (*Seasonal AutoRegressive Integrated Moving Average*) e um modelo estatistico classico de series temporais. Ele combina tres ideias: a parte autorregressiva (AR), que usa valores passados da serie; a parte de media movel (MA), que usa erros passados; e a diferenciacao (I, de *integrated*), que remove tendencia para tornar a serie estacionaria. O "S" acrescenta componentes sazonais, que capturam o padrao que se repete a cada ciclo (aqui, o ciclo anual da gripe).

**Fonte original.** Box, G. E. P.; Jenkins, G. M. (metodologia Box-Jenkins). Tratamento didatico moderno em Hyndman, R. J.; Athanasopoulos, G., *Forecasting: Principles and Practice* ([otexts.com/fpp3](https://otexts.com/fpp3/)). Implementacao usada: [statsmodels SARIMAX](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html).

**Onde no projeto.** Em `backend/app/model/walk_forward.py`, a funcao `preditor_sarima`, que usa a classe `SARIMAX` do `statsmodels.tsa.statespace.sarimax`.

**Como foi aplicada.** A funcao recebe a ordem nao sazonal e a ordem sazonal como parametros, ajusta o `SARIMAX` sobre o historico de cada passo do walk-forward (com `enforce_stationarity=False` e `enforce_invertibility=False`, que relaxam restricoes de ajuste para evitar falhas de convergencia) e preve o bloco seguinte. As previsoes tambem sao limitadas a valores nao negativos.

**Numero real.** MAE 7,51 (o MENOR MAE entre todos os modelos), RMSE 23,34, sMAPE 44,53%.

**Como interpretar.** O SARIMA obteve o menor erro absoluto medio do estudo. Isso reforca a leitura honesta: num problema de serie temporal com sazonalidade, um modelo estatistico desenhado para o tempo pode superar o Random Forest. Mesmo assim, como se vera na secao 8, a diferenca do Random Forest para o SARIMA nao foi estatisticamente significativa.

---

## 6. Prophet

**O que e.** O Prophet e um modelo de previsao desenvolvido pelo Facebook/Meta. Ele e aditivo: decompoe a serie em componentes somadas, principalmente tendencia e sazonalidade (e, opcionalmente, feriados). A ideia e ajustar uma curva de tendencia suave somada a padroes sazonais periodicos, de forma robusta a dados faltantes e a mudancas de tendencia.

**Fonte original.** Taylor, S. J.; Letham, B. (2018). "Forecasting at scale". *The American Statistician*, 72(1), 37-45. Pre-print disponivel em [peerj.com/preprints/3190](https://peerj.com/preprints/3190/). Documentacao: [facebook.github.io/prophet](https://facebook.github.io/prophet/).

**Onde no projeto.** Em `backend/app/model/walk_forward.py`, a funcao `preditor_prophet`.

**Como foi aplicada.** O Prophet exige uma coluna de datas; o codigo constroi datas semanais sinteticas (frequencia de 7 dias a partir de uma origem fixa) para preservar a ordem e a sazonalidade anual sem depender do calendario epidemiologico exato. O modelo e configurado com sazonalidade anual ativada (`yearly_seasonality=True`) e sazonalidades diaria e semanal desligadas, ajustado sobre o historico de cada passo e usado para prever o bloco. As previsoes negativas sao zeradas.

**Numero real.** MAE 10,38, RMSE 23,07, sMAPE 46,96%.

**Como interpretar.** O Prophet teve o maior MAE entre os modelos (10,38), o que indica que, nesta serie curta e esparsa, sua decomposicao tendencia mais sazonalidade nao se ajustou tao bem quanto as alternativas. E um resultado util de reportar: nem todo modelo popular e automaticamente melhor para todo problema.

---

## 7. Metricas de avaliacao (MAE, RMSE, MAPE, sMAPE, acerto direcional)

**O que e.** Metricas de erro medem o quanto a previsao se afasta do observado.
- **MAE** (erro medio absoluto): a media de `|real - previsto|`. Facil de interpretar, na mesma unidade dos casos.
- **RMSE** (raiz do erro quadratico medio): penaliza mais os erros grandes, porque eleva ao quadrado antes de tirar a media. Sensivel a picos.
- **MAPE** (erro percentual absoluto medio): erro em porcentagem. Problema: divide pelo valor real, entao e indefinido quando o real e zero. Como a serie tem muitas semanas de zero casos, o MAPE classico so pode ser calculado nas semanas com real maior que zero.
- **sMAPE** (MAPE simetrico): divide pela soma dos modulos de real e previsto, por isso e finito mesmo com zeros. Foi a metrica percentual adotada por causa da esparsidade da serie.
- **Acerto direcional**: proporcao de vezes em que o modelo acertou a direcao (subida ou descida) entre semanas consecutivas.

**Fonte original.** Hyndman, R. J.; Koehler, A. B. (2006). "Another look at measures of forecast accuracy". *International Journal of Forecasting*, 22(4), 679-688. Disponivel em [sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0169207006000239).

**Onde no projeto.** Em `backend/app/model/metricas.py`: `mae`, `rmse`, `mape` (restrito a `real > 0`), `smape`, `acerto_direcional` e a funcao agregadora `calcular_metricas` (que tambem reporta `semanas_ignoradas_mape`).

**Como foi aplicada.** A funcao `mape` filtra os pontos com real diferente de zero antes de dividir, evitando a divisao por zero, e retorna NaN se todos os reais forem zero. A funcao `smape` trata o caso de real e previsto ambos zero como erro zero (previsao perfeita de ausencia de casos). A `calcular_metricas` conta quantas semanas de zero caso foram descartadas do MAPE classico.

**Numero real.** Foram **242 semanas ignoradas** no MAPE classico (semanas de zero casos). Por isso o sMAPE e a metrica percentual reportada no corpo do trabalho.

**Como interpretar.** O argumento de defesa e que a escolha do sMAPE nao foi arbitraria: o MAPE classico simplesmente nao se aplica a 242 semanas da serie (divisao por zero), e esconder isso seria desonesto. Reportar quantas semanas foram ignoradas e, junto, usar o sMAPE demonstra tratamento correto de serie esparsa.

---

## 8. Teste de Diebold-Mariano

**O que e.** O teste de Diebold-Mariano (DM) verifica se a diferenca de acuracia entre dois modelos de previsao e estatisticamente significativa, ou se pode ser fruto do acaso. E a ferramenta formal que permite (ou nao) afirmar que um modelo e superior ao outro.

> **Registro importante (defender com dominio).** No projeto, o Diebold-Mariano foi **implementado a mao, em Python puro**, e nao copiado de uma biblioteca. A implementacao calcula as autocovariancias do diferencial de perda, aplica a correcao de amostra pequena de Harvey-Leybourne-Newbold (HLN) e obtem o p-valor pela distribuicao t de Student, com a cauda da t avaliada pela funcao beta incompleta regularizada via fracao continua de Lentz (quando o scipy nao esta disponivel). Por ser uma implementacao artesanal, o aluno precisa dominar a matematica a seguir; a banca pode perguntar.

**A matematica, de forma didatica.**
- Sejam `e1_t` e `e2_t` os erros de previsao dos modelos 1 e 2 no instante `t`. Aqui o modelo 1 e o Random Forest.
- A funcao de perda e o erro quadratico, `g(e) = e^2`. O diferencial de perda e `d_t = e1_t^2 - e2_t^2`.
- Sob a hipotese nula (H0) de igual acuracia, a media esperada do diferencial e zero: `E[d_t] = 0`.
- A estatistica do teste e `DM = media(d) / raiz(variancia de longo prazo da media de d)`. A variancia de longo prazo soma a variancia (`gamma_0`) mais o dobro das autocovariancias ate a defasagem `h - 1`, onde `h` e o horizonte.
- A correcao HLN multiplica a estatistica por um fator que depende de `n` e de `h`, corrigindo o vies em amostras pequenas, e o resultado e comparado a uma distribuicao **t de Student** com `n - 1` graus de liberdade.
- Interpretacao do sinal (com perda quadratica e modelo 1 = Random Forest): **`DM < 0` favorece o Random Forest** (erro quadratico menor que o do comparador); `DM > 0` favorece o comparador.

**Fonte original.** Diebold, F. X.; Mariano, R. S. (1995). "Comparing Predictive Accuracy". *Journal of Business & Economic Statistics*, 13(3), 253-263. Disponivel em [tandfonline.com](https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599). Correcao de amostra pequena: Harvey, D.; Leybourne, S.; Newbold, P. (1997). "Testing the equality of prediction mean squared errors". *International Journal of Forecasting*, 13(2), 281-291. Disponivel em [sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0169207096007194).

**Onde no projeto.** Em `backend/app/model/significancia.py`: a funcao `diebold_mariano` (estatistica, correcao HLN e decisao) e as auxiliares de p-valor `_p_valor_bicaudal_t`, `_beta_incompleta_regularizada` e `_fracao_continua_beta`.

**Como foi aplicada.** A funcao recebe os erros pareados do Random Forest e do comparador, monta o diferencial de perda quadratica, calcula a variancia de longo prazo pelas autocovariancias, aplica a correcao HLN e devolve o p-valor bicaudal pela t de Student. Quando a variancia de longo prazo nao e positiva, o codigo retorna p-valor 1,0 (sem evidencia de diferenca).

**Numero real.** Random Forest frente a cada comparador: contra o baseline p = 0,5117 (nao significativo); contra o SARIMA p = 0,3365 (nao significativo); contra o Prophet p = 0,5422 (nao significativo).

**Como interpretar.** Em todos os comparadores o p-valor ficou bem acima de 0,05, ou seja, **nenhuma diferenca foi estatisticamente significativa**. Por isso o Random Forest NAO e apresentado como superior: nao ha evidencia formal de que ele seja melhor nem pior que os outros. Essa e exatamente a postura honesta esperada.

> **Nota didatica (alternativa de biblioteca).** Por ser uma implementacao artesanal, voce precisa dominar a matematica acima para defende-la. Se preferir defender via biblioteca consagrada, existe a alternativa de usar implementacoes de referencia (por exemplo, rotinas do `statsmodels` ou a implementacao `dm_test` amplamente citada). A escolha de implementar a mao foi para ter controle total e rastreabilidade do calculo; a alternativa de biblioteca e legitima e pode ser citada na banca.

---

## 9. Teste de Wilcoxon dos postos com sinais

**O que e.** O teste de Wilcoxon dos postos com sinais (*Wilcoxon signed-rank test*) e um teste nao parametrico: ele nao assume que os dados seguem distribuicao normal, o que o torna adequado a series curtas e esparsas. Em vez de comparar medias, ele compara os postos (as posicoes na ordenacao) das diferencas pareadas. No projeto, e aplicado aos erros absolutos pareados dos dois modelos.

**Fonte original.** Wilcoxon, F. (1945). "Individual Comparisons by Ranking Methods". *Biometrics Bulletin*, 1(6), 80-83. Implementacao usada: [scipy.stats.wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).

**Onde no projeto.** Em `backend/app/model/significancia.py`, a funcao `wilcoxon_erros`, que delega o calculo a `scipy.stats.wilcoxon`.

**Como foi aplicada.** A funcao toma os erros absolutos `|erro|` de cada modelo, par a par, e aplica `wilcoxon(abs_modelo, abs_comparador, zero_method="wilcox")`. Se todos os erros absolutos forem identicos, retorna p-valor 1,0 (nada a testar). Tambem compara as medianas dos erros absolutos para indicar qual modelo teve o menor erro mediano.

**Numero real.** Random Forest contra baseline p = 0,0006 (significativo); contra SARIMA p = 0,4824 (nao significativo); contra Prophet p = 0,0 (significativo).

**Como interpretar (Wilcoxon frente ao Diebold-Mariano).** A primeira vista parece contradizer o DM: o Wilcoxon acusa diferenca significativa contra o baseline e contra o Prophet, enquanto o DM nao acusa diferenca em nenhum caso. Nao e contradicao, e informacao complementar, porque os dois testes medem coisas diferentes:
- O **Diebold-Mariano** usa a perda quadratica media, por isso e muito sensivel a poucos erros grandes (os picos). Numa serie com picos, uns poucos erros enormes dominam a variancia e dificultam atingir significancia.
- O **Wilcoxon** usa os postos dos erros absolutos pareados, por isso e sensivel a diferencas sistematicas de magnitude, mesmo quando sao pequenas e consistentes ao longo de muitas semanas.
Em resumo: o Wilcoxon pode captar uma diferenca sistematica pequena que o DM nao enxerga por estar focado no erro quadratico dos picos.

**Leitura final conservadora.** Como o teste principal (Diebold-Mariano) nao foi significativo em nenhum comparador, e como o Wilcoxon contra o baseline aponta diferenca mas o MAE do baseline e menor que o do Random Forest, a conclusao honesta e: **nao ha evidencia robusta de superioridade do Random Forest**. O modelo e entregue por completude de escopo, com desempenho relatado de forma transparente.

---

## 10. Stack de tecnologias (entradas resumidas)

Esta secao e um apoio rapido. Diferente das 9 tecnicas de modelagem, aqui basta saber o que e cada ferramenta, onde foi usada e a fonte.

- **FastAPI** (framework web Python para a API REST). O que e: framework de alta performance para construir APIs em Python, com validacao automatica. Onde: `backend/app/` (ponto de entrada `backend/app/main.py`). Link: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/).
- **SQLAlchemy** (mapeamento objeto-relacional, ORM). O que e: biblioteca que mapeia tabelas do banco para classes Python e gerencia conexoes. Onde: `backend/app/models/orm.py` (modelos) e `backend/app/db.py` (conexao). Link: [docs.sqlalchemy.org](https://docs.sqlalchemy.org/en/20/).
- **PostgreSQL e Terceira Forma Normal (3FN)**. O que e: banco de dados relacional; a 3FN e uma regra de normalizacao que elimina redundancia e dependencias transitivas, mantendo integridade. Onde: `database/schema.sql` (esquema), `database/indexes.sql` e `database/seed.sql`. Link: [postgresql.org/docs](https://www.postgresql.org/docs/).
- **pandas** (manipulacao de dados tabulares). O que e: biblioteca Python para carregar, limpar e transformar tabelas (DataFrames). Onde: scripts de ETL em `scripts/etl_coleta.py`, `scripts/etl_tratamento.py` e `scripts/etl_utils.py`. Link: [pandas.pydata.org/docs](https://pandas.pydata.org/docs/).
- **Next.js e Recharts** (painel web). O que e: Next.js e o framework React para o frontend; Recharts e a biblioteca de graficos. Onde: `frontend/`. Links: [nextjs.org/docs](https://nextjs.org/docs) e [recharts.org](https://recharts.org/).
- **Ponte CNES para distrito via GeoSampa** (analise exploratoria complementar). O que e: metodo que resolve o distrito do hospital notificante a partir do endereco publico do cadastro CNES cruzado com as camadas territoriais do GeoSampa. Onde: `docs/tcc/ponte_cnes/`. Links: [opendatasus.saude.gov.br](https://opendatasus.saude.gov.br/) e [geosampa.prefeitura.sp.gov.br](https://geosampa.prefeitura.sp.gov.br/). Limitacao a declarar: o distrito identificado e o do hospital, nao o da residencia do paciente.

---

## 11. Tabela-resumo e pontos de defesa de banca

**Tabela consolidada (numeros reais de `docs/metricas_modelos.md`).**

| Modelo | MAE | RMSE | sMAPE | Acerto direcional | DM (p-valor) | Wilcoxon (p-valor) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 8,2846 | 22,8614 | 47,3293% | 0,5125 | 0,5117 (nao signif.) | 0,0006 (signif.) |
| random_forest (referencia) | 8,5628 | 25,4827 | 37,5097% | 0,5308 | referencia | referencia |
| sarima | 7,5123 | 23,343 | 44,5322% | 0,4823 | 0,3365 (nao signif.) | 0,4824 (nao signif.) |
| prophet | 10,3754 | 23,0694 | 46,9626% | 0,5321 | 0,5422 (nao signif.) | 0,0 (signif.) |

Observacoes: os p-valores de DM e Wilcoxon sao do Random Forest frente a cada comparador. No MAPE classico, **242 semanas de zero casos foram ignoradas**, motivo pelo qual o sMAPE e a metrica percentual reportada.

**Pontos de defesa de banca (perguntas provaveis e respostas).**

- **Por que o modelo complexo (Random Forest) nao venceu o baseline simples?** Em series temporais curtas e esparsas, com muitas semanas de zero casos e poucos picos, um modelo complexo tem pouca informacao para aprender padroes robustos e tende a nao extrapolar bem os picos (o Random Forest nao projeta valores acima do maximo observado). O baseline sazonal, por outro lado, acerta bem a parte repetitiva da serie. Empatar ou perder para o baseline nesse cenario e esperado e e um resultado legitimo, nao um defeito do trabalho.
- **Por que entregar o Random Forest mesmo sem superioridade comprovada?** Por completude do escopo e para comparacao transparente. O trabalho se compromete a reportar o desempenho real, nao a inventar superioridade.
- **Por que o Diebold-Mariano e o Wilcoxon divergem?** Porque medem coisas diferentes: o DM usa perda quadratica media (sensivel a poucos erros grandes nos picos), e o Wilcoxon usa postos de erros absolutos pareados (sensivel a diferencas sistematicas de magnitude). Nao e contradicao, e complemento. A leitura final conservadora e que nao ha evidencia robusta de superioridade do Random Forest, porque o teste principal (DM) nao foi significativo em nenhum comparador.
- **Por que usar sMAPE e nao MAPE?** Porque o MAPE classico divide pelo valor real e e indefinido em 242 semanas de zero casos; o sMAPE e finito mesmo com zeros, sendo a escolha correta para serie esparsa.
- **Como garantir que nao houve vazamento de dados?** A engenharia de atributos usa somente informacao passada em cada linha, e a validacao walk-forward mantem o teste sempre posterior ao treino (origem expansiva), com todos os modelos sob o mesmo protocolo.
- **O Diebold-Mariano foi implementado a mao: voce domina a matematica?** Sim: diferencial de perda quadratica `d_t = e1^2 - e2^2`, hipotese nula `E[d_t] = 0`, estatistica `DM = media(d) / raiz(variancia de longo prazo)`, correcao HLN de amostra pequena e comparacao com a t de Student. Existe tambem a alternativa de usar bibliotecas de referencia, caso se prefira defender por biblioteca.
