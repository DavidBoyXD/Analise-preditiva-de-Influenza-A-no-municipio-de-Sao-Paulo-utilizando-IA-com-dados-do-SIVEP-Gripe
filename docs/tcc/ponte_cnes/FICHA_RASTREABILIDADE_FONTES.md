# Ficha de Rastreabilidade das Fontes (FEAT-001)

Documento gerado automaticamente por 01_download_fontes.py. Registra a procedencia de cada fonte publica utilizada na investigacao exploratoria da ponte CNES -> distrito de Sao Paulo.

Gerado em: 2026-10-01 02:36:23 UTC

## Microdados SRAG 2024 (amostra SP capital)

- Arquivo gerado: `srag_amostra_sp_2024.csv`
- Fonte: openDATASUS / Ministerio da Saude - SIVEP-Gripe
- URL: https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2024/INFLUD24-23-03-2026.csv
- Data/hora de extracao: 2026-10-01 02:36:12 UTC
- Tamanho: 2670220 bytes
- Linhas lidas na origem: 267986
- Linhas retidas (recorte SP): 18574
- Colunas presentes: NU_NOTIFIC, DT_NOTIFIC, SEM_NOT, SEM_PRI, DT_SIN_PRI, CO_MUN_NOT, ID_MUNICIP, CO_MUN_RES, CS_ZONA, NM_UN_INTE, ID_RG_INTE, CO_RG_INTE
- Colunas ausentes no header: nenhuma
- Coluna usada no filtro de municipio: CO_MUN_NOT
- Observacoes: Retidas apenas linhas com CO_MUN_NOT=355030.

## Microdados SRAG 2013 (amostra SP capital)

- Arquivo gerado: `srag_amostra_sp_2013.csv`
- Fonte: openDATASUS / Ministerio da Saude - SIVEP-Gripe
- URL: https://d26692udehoye.cloudfront.net/SRAG/2013-2018/INFLUD13.csv
- Data/hora de extracao: 2026-10-01 02:36:12 UTC
- Tamanho: 150743 bytes
- Linhas lidas na origem: 36641
- Linhas retidas (recorte SP): 4073
- Colunas presentes: DT_NOTIFIC, SEM_NOT, DT_SIN_PRI, ID_MUNICIP
- Colunas ausentes no header: NU_NOTIFIC, SEM_PRI, CO_MUN_NOT, CO_MUN_RES, CS_ZONA, NM_UN_INTE, ID_RG_INTE, CO_RG_INTE
- Coluna usada no filtro de municipio: ID_MUNICIP
- Observacoes: CO_MUN_NOT ausente neste ano; retidas apenas linhas com ID_MUNICIP=355030 (codigo da capital de Sao Paulo). Observacao: este ano tambem nao possui NM_UN_INTE (nome da unidade de internacao), de modo que a ponte por nome de hospital nao e aplicavel a 2013.

## Cadastro CNES de estabelecimentos (recorte SP capital)

- Arquivo gerado: `cnes_sp_estabelecimentos.csv`
- Fonte: CNES / DATASUS - cnes_estabelecimentos.csv (via zip ja baixado)
- URL: https://cnes.datasus.gov.br (arquivo cnes_estabelecimentos_csv.zip)
- Data/hora de extracao: 2026-10-01 02:36:15 UTC
- Tamanho: 7031774 bytes
- Linhas lidas na origem: 637992
- Linhas retidas (recorte SP): 43755
- Colunas presentes: CO_CNES, CO_UNIDADE, CO_IBGE, NO_RAZAO_SOCIAL, NO_FANTASIA, TP_UNIDADE, CO_CEP, NO_LOGRADOURO, NU_ENDERECO, NO_BAIRRO, NU_LATITUDE, NU_LONGITUDE
- Colunas ausentes no header: nenhuma
- Percentual com latitude/longitude: 79.2%
- Percentual com bairro: 100.0%
- Percentual com CEP: 100.0%
- Observacoes: Retidos estabelecimentos com CO_IBGE em {3550308, 355030}.

## GeoSampa - camada geoportal:distrito_municipal

- Arquivo gerado: `geosampa_distritos.geojson`
- Fonte: GeoSampa / Prefeitura de Sao Paulo (WFS)
- URL: http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=geoportal:distrito_municipal&outputFormat=application/json&count=1000
- Data/hora de extracao: 2026-10-01 02:36:20 UTC
- Tamanho: 5055267 bytes
- Numero de features: 96
- CRS declarado: urn:ogc:def:crs:EPSG::31983
- Observacoes: CRS esperado EPSG:31983 (SIRGAS 2000 / UTM 23S).

## GeoSampa - camada geoportal:subprefeitura

- Arquivo gerado: `geosampa_subprefeituras.geojson`
- Fonte: GeoSampa / Prefeitura de Sao Paulo (WFS)
- URL: http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=geoportal:subprefeitura&outputFormat=application/json&count=1000
- Data/hora de extracao: 2026-10-01 02:36:23 UTC
- Tamanho: 3110810 bytes
- Numero de features: 32
- CRS declarado: urn:ogc:def:crs:EPSG::31983
- Observacoes: CRS esperado EPSG:31983 (SIRGAS 2000 / UTM 23S).
