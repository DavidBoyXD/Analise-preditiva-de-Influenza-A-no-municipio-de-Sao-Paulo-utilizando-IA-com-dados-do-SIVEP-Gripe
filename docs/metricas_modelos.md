# Tabela comparativa de metricas dos modelos (RF004)

Metricas obtidas sob validacao cronologica walk-forward (origem expansiva, horizonte de 6 semanas) sobre a serie de treino do municipio de Sao Paulo.

- **mae / rmse**: erro medio absoluto e raiz do erro quadratico medio.
- **mape_semanas_positivas**: MAPE classico calculado apenas em semanas com real > 0 (evita divisao por zero); **semanas_ignoradas_mape** conta as semanas de zero casos descartadas.
- **smape**: MAPE simetrico, finito mesmo com zeros.
- **acerto_direcional**: proporcao de acerto na direcao (subida/descida).
- **dm_**: teste de Diebold-Mariano do RF frente ao comparador (perda quadratica). DM < 0 favorece o Random Forest.
- **wilcoxon_**: teste nao parametrico de Wilcoxon sobre os erros absolutos.

| modelo | mae | rmse | mape_semanas_positivas | smape | acerto_direcional | semanas_ignoradas_mape | dm_estatistica | dm_p_valor | dm_significativo | wilcoxon_p_valor | wilcoxon_significativo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 8.2846 | 22.8614 | 97.8533 | 47.3293 | 0.5125 | 242 | 0.6565 | 0.5117 | nao | 0.0006 | sim |
| random_forest | 8.5628 | 25.4827 | 123.8018 | 37.5097 | 0.5308 | 242 | (referencia) |  |  |  |  |
| sarima | 7.5123 | 23.343 | 97.0123 | 44.5322 | 0.4823 | 242 | 0.9617 | 0.3365 | nao | 0.4824 | nao |
| prophet | 10.3754 | 23.0694 | 251.922 | 46.9626 | 0.5321 | 242 | 0.6098 | 0.5422 | nao | 0.0 | sim |
