# Tabela comparativa de metricas dos modelos - EXPERIMENTO DE VALIDACAO (Dengue)

**Enquadramento:** experimento ISOLADO e NAO-INTEGRADO ao TCC. A Dengue NAO faz parte do objeto oficial do projeto (que continua Influenza A / municipio de Sao Paulo). Reaplicacao da MESMA metodologia sobre uma segunda serie para validacao.

Metricas obtidas sob validacao cronologica walk-forward (origem expansiva, horizonte de 6 semanas) sobre a serie semanal de Dengue do municipio de Sao Paulo (InfoDengue, 2010-2024).

- **mae / rmse**: erro medio absoluto e raiz do erro quadratico medio.
- **mape_semanas_positivas**: MAPE classico calculado apenas em semanas com real > 0 (evita divisao por zero); **semanas_ignoradas_mape** conta as semanas de zero casos descartadas.
- **smape**: MAPE simetrico, finito mesmo com zeros.
- **acerto_direcional**: proporcao de acerto na direcao (subida/descida).
- **dm_**: teste de Diebold-Mariano do RF frente ao comparador (perda quadratica). DM < 0 favorece o Random Forest.
- **wilcoxon_**: teste nao parametrico de Wilcoxon sobre os erros absolutos.

| modelo | mae | rmse | mape_semanas_positivas | smape | acerto_direcional | semanas_ignoradas_mape | dm_estatistica | dm_p_valor | dm_significativo | wilcoxon_p_valor | wilcoxon_significativo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 2147.4285 | 9997.5144 | 109.89 | 35.4869 | 0.6519 | 0 | -0.9262 | 0.3547 | nao | 0.0 | sim |
| random_forest | 1388.2715 | 6467.8756 | 46.9795 | 17.8855 | 0.613 | 0 | (referencia) |  |  |  |  |
| sarima | 1310.7079 | 7092.0996 | 43.7522 | 22.2946 | 0.5548 | 0 | -0.3826 | 0.7022 | nao | 0.0169 | sim |
| prophet | 2401.6853 | 9301.6517 | 179.9007 | 53.5398 | 0.484 | 0 | -0.9146 | 0.3607 | nao | 0.0 | sim |
