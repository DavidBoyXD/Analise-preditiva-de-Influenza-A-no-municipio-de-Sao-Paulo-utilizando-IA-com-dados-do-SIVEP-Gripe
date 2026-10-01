# Relatorio de Cobertura da Ponte Hospital Notificante -> Distrito

Investigacao exploratoria e isolada (nao integrada ao repositorio do TCC). A regiao intramunicipal (distrito, subprefeitura e zona) e derivada do endereco publico do HOSPITAL de internacao informado em NM_UN_INTE, cruzado com o registro CNES e com as camadas territoriais do GeoSampa.

## Observacao metodologica (LGPD e interpretacao)

O distrito atribuido e o do estabelecimento de internacao, obtido de dado publico (CNES). Nao se usa nenhum dado de residencia do paciente nem informacao individual identificavel. A serie temporal e sempre agregada por semana epidemiologica mais distrito-do-hospital. Vale lembrar que o distrito do HOSPITAL nao equivale ao distrito de RESIDENCIA do paciente: hospitais de referencia atraem casos de toda a cidade, o que concentra contagens nos distritos que sediam grandes unidades.

## Casamento de nomes distintos de unidade (NM_UN_INTE) ao CNES

- Nomes distintos de unidade processados: 148
- Casados por match exato normalizado: 140 (94.6%)
- Casados por match aproximado (rapidfuzz token_sort_ratio >= 90): 0 (0.0%)
- Nao encontrados no CNES: 8 (5.4%)
- Nomes distintos resolvidos a um distrito: 139 (93.9%)

## Cobertura por ano (ponderada por volume de casos)

### Ano 2013

- Total de casos SP capital: 4073
- A amostra deste ano NAO possui a coluna NM_UN_INTE (nome do hospital de internacao). A ponte por nome de hospital NAO se aplica a este ano, portanto nenhum caso foi atribuido a distrito. Registrado de forma explicita e defensiva, sem interromper o processamento.

### Ano 2024

- Total de casos SP capital: 18574
- Casos com NM_UN_INTE preenchido: 17040 (91.7%)
- Casos resolvidos a um distrito: 16722 (90.0%)
  - por ponto (lat/long point-in-polygon): 16150 (86.9%)
  - por fallback de bairro: 572 (3.1%)
- Casos nao mapeados a distrito: 1852 (10.0%)

#### 15 distritos com mais casos (2024)

| Distrito | Casos | % do total do ano |
| --- | --- | --- |
| BELA VISTA | 4230 | 22.8% |
| BOM RETIRO | 1498 | 8.1% |
| CONSOLACAO | 1206 | 6.5% |
| VILA MARIANA | 979 | 5.3% |
| MORUMBI | 916 | 4.9% |
| VILA PRUDENTE | 877 | 4.7% |
| JARDIM SAO LUIS | 815 | 4.4% |
| MOOCA | 566 | 3.0% |
| SANTANA | 546 | 2.9% |
| BELEM | 521 | 2.8% |
| PIRITUBA | 461 | 2.5% |
| JARDIM PAULISTA | 379 | 2.0% |
| JACANA | 373 | 2.0% |
| MOEMA | 329 | 1.8% |
| CAMPO GRANDE | 310 | 1.7% |

## Resumo de aplicabilidade

- Anos com NM_UN_INTE (ponte aplicavel): 2024
- Anos sem NM_UN_INTE (ponte nao aplicavel): 2013

Arquivos gerados em saida/: crosswalk_unidade_distrito.csv e serie_temporal_por_distrito.csv.
