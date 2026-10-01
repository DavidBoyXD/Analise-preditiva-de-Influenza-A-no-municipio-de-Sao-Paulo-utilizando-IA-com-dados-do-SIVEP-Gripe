# Relatório de Viabilidade da Ponte Hospital Notificante para Região Intramunicipal de São Paulo

Investigação exploratória, isolada e NÃO integrada ao repositório do TCC. Este documento consolida as evidências levantadas nos scripts `01_download_fontes.py` e `02_construir_crosswalk.py` e nos relatórios de cobertura já apurados. Nenhum número foi reexecutado para este relatório: todos os valores citados vêm de `saida/RELATORIO_COBERTURA.md` e de `dados_brutos/FICHA_RASTREABILIDADE.md`.

Objetivo da investigação: verificar se é possível, a partir do hospital/unidade que notificou ou internou cada caso de SRAG/Influenza, derivar uma "região" intramunicipal da cidade de São Paulo (distrito, subprefeitura, zona e bairro), mesmo que os microdados do SIVEP-Gripe/SINAN/DATASUS não tragam esse recorte geográfico de forma direta. O escopo é apenas o município de São Paulo (código 355030 / 3550308).

## Sumário do veredicto

**PARCIALMENTE VIÁVEL.** A ponte funciona e é robusta para os anos recentes que trazem o nome do hospital de internação (`NM_UN_INTE`): em 2024, 90,0% dos casos notificados na capital foram resolvidos a um distrito. Porém a ponte NÃO se aplica aos anos antigos que não possuem o campo `NM_UN_INTE` (confirmado em 2013), e carrega uma limitação metodológica central: o distrito derivado é o do HOSPITAL, não o da residência do paciente. A fundamentação completa está na seção 7.

---

## 1. (a) Os microdados brutos do SIVEP-Gripe de 2009-2019 e 2022-2026 estão disponíveis publicamente?

**SIM, publicamente e sem credencial.** Os microdados brutos de SRAG/SIVEP-Gripe são distribuídos no Portal de Dados Abertos do SUS (dadosabertos.saude.gov.br), organizados em três datasets por período, com um arquivo INFLUD por ano:

- Dataset `srag-2009-2012` (cobre 2009 a 2012).
- Dataset `srag-2013-2018` (cobre 2013 a 2018).
- Dataset `srag-2019-a-2026` (cobre 2019 em diante, até 2026).

Os arquivos ficam hospedados em S3/CloudFront. Exemplos de URL efetivamente usados nesta investigação (registrados em `dados_brutos/FICHA_RASTREABILIDADE.md`):

- 2024: `https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2024/INFLUD24-23-03-2026.csv`
- 2013: `https://d26692udehoye.cloudfront.net/SRAG/2013-2018/INFLUD13.csv`

A cobertura temporal dos datasets (2009 a 2026) atende integralmente ao período do projeto (2009-2019 e 2022-2026). O download foi feito via streaming, sem necessidade de login.

## 2. (b) Esses microdados contêm identificação da unidade notificante / CNES?

**Resposta com nuance (verificada).** O DICIONÁRIO de dados do SIVEP (`DIC_DADOS_Influenza_v6 2023.pdf`, no repositório do projeto) define os campos:

- `CO_UNI_NOT` / `ID_UNIDADE`: código CNES da unidade notificante (campo obrigatório).
- `CO_UN_INTE` / `ID_UN_INTE`: código CNES da unidade de internação (campo essencial).

**PORÉM, o CSV público NÃO expõe o CÓDIGO CNES.** Essa coluna foi suprimida do open data. O que o CSV de 2024 (194 colunas na origem) efetivamente expõe, e que foi retido no recorte da capital, é:

- `CO_MUN_NOT`: código do município de notificação (usado como filtro, valor 355030 para a capital).
- `ID_RG_INTE` / `CO_RG_INTE`: regional de saúde da internação.
- `NM_UN_INTE`: o NOME do estabelecimento de internação, em texto livre (string).

Ou seja, há identificação do estabelecimento, mas por NOME, não por código CNES. Isso define toda a estratégia da ponte (seção 3). As colunas efetivamente presentes no recorte de 2024 foram: `NU_NOTIFIC, DT_NOTIFIC, SEM_NOT, SEM_PRI, DT_SIN_PRI, CO_MUN_NOT, ID_MUNICIP, CO_MUN_RES, CS_ZONA, NM_UN_INTE, ID_RG_INTE, CO_RG_INTE`.

## 3. (c) O cadastro CNES é obtível e cruza com esses identificadores?

**SIM.** O cadastro de estabelecimentos CNES é público (`cnes_estabelecimentos.csv`, distribuído em `cnes_estabelecimentos_csv.zip` por cnes.datasus.gov.br). O recorte da capital (`CO_IBGE` em {3550308, 355030}) resultou em **43.755 estabelecimentos**, com as colunas: `CO_CNES, CO_UNIDADE, CO_IBGE, NO_RAZAO_SOCIAL, NO_FANTASIA, TP_UNIDADE, CO_CEP, NO_LOGRADOURO, NU_ENDERECO, NO_BAIRRO, NU_LATITUDE, NU_LONGITUDE`.

Qualidade desse recorte: **100,0% com bairro, 100,0% com CEP e 79,2% com latitude/longitude.**

Como o código CNES foi suprimido do SRAG, o cruzamento NÃO é feito por código. Ele é feito por NOME do estabelecimento: `NM_UN_INTE` (do SRAG) é casado contra `NO_FANTASIA` / `NO_RAZAO_SOCIAL` (do CNES filtrado por município), usando normalização de texto (maiúsculas, remoção de acentos, expansão de abreviações) seguida de match exato e, como complemento, match aproximado (rapidfuzz, `token_sort_ratio >= 90`).

Resultado do casamento de nomes distintos (ano 2024, conforme `RELATORIO_COBERTURA.md`):

- Nomes distintos de unidade processados: **148**
- Casados por match exato normalizado: **140 (94,6%)**
- Casados por match aproximado (fuzzy): **0 (0,0%)**
- Não encontrados no CNES: **8 (5,4%)**
- Nomes distintos resolvidos a um distrito: **139 (93,9%)**

## 4. (d) Consegue-se mapear estabelecimento para distrito / subprefeitura / bairro de SP?

**SIM.** O mapeamento usa a latitude/longitude do CNES combinada a um join espacial point-in-polygon contra as camadas territoriais públicas do GeoSampa (Prefeitura de São Paulo, acessadas via WFS GetFeature como GeoJSON):

- `geoportal:distrito_municipal`: **96 distritos**, CRS EPSG:31983 (SIRGAS 2000 / UTM 23S), com os atributos `nm_distrito_municipal`, `cd_identificador_subprefeitura` e `nm_regiao_05` (zona).
- `geoportal:subprefeitura`: **32 subprefeituras**, mesmo CRS.

A resolução geográfica alcançada é: **distrito > subprefeitura > zona**. Além disso, o **bairro** vem direto do campo `NO_BAIRRO` do CNES (100% preenchido no recorte da capital), também público. Para estabelecimentos sem coordenada (os ~20,8% sem lat/long), existe um fallback que atribui o distrito a partir do bairro do CNES.

A crosswalk resultante (`saida/crosswalk_unidade_distrito.csv`) traz as colunas: `nm_un_inte_original, nm_un_inte_normalizado, co_cnes, no_fantasia_cnes, no_bairro, co_cep, latitude, longitude, distrito, cd_subprefeitura, zona_regiao05, metodo_match, score_match, metodo_distrito`.

## 5. (e) Qual a cobertura real?

Os números abaixo vêm de `saida/RELATORIO_COBERTURA.md` (ponderados por volume de casos).

### Ano 2024 (ponte aplicável)

- Total de casos SP capital (`CO_MUN_NOT=355030`): **18.574**
- Casos com `NM_UN_INTE` preenchido: **17.040 (91,7%)**
- Casos resolvidos a um distrito: **16.722 (90,0%)**
  - por ponto (lat/long point-in-polygon): **16.150 (86,9%)**
  - por fallback de bairro: **572 (3,1%)**
- Casos não mapeados a distrito: **1.852 (10,0%)**

### Ano 2013 (ponte NÃO aplicável)

- Total de casos SP capital: **4.073**
- A amostra de 2013 (INFLUD13) NÃO possui a coluna `NM_UN_INTE`. A ponte por nome de hospital não se aplica a este ano, portanto nenhum caso foi atribuído a distrito. Registrado de forma explícita e defensiva, sem interromper o processamento.

**Síntese de cobertura:** para o ano recente testado, 9 em cada 10 casos notificados na capital receberam um distrito. Para o ano antigo testado, a cobertura é zero por ausência do campo de unidade.

## 6. (f) Principais limitações e vieses

1. **Dependência do campo `NM_UN_INTE`.** A ponte só funciona nos anos em que esse campo existe e vem preenchido. Confirmado que 2013 não o possui (ver seção 8). É preciso confirmar a partir de qual ano o campo passou a existir; nos dados do projeto 2009-2019, grande parte dos primeiros anos pode não ter esse campo.
2. **Distrito do hospital, não da residência (limitação central).** Detalhada na seção 7.
3. **Nomes não casados.** 5,4% dos nomes distintos de 2024 (8 nomes) não foram encontrados no CNES, e 10,0% dos casos de 2024 não foram mapeados a distrito (soma de nome em branco, nome não casado e estabelecimento sem coordenada nem bairro resolvível).
4. **Cobertura espacial do CNES.** 79,2% dos estabelecimentos têm coordenada; o restante depende do fallback por bairro, de menor precisão.
5. **Variação de grafia e abreviação** em `NM_UN_INTE` (texto livre) exige normalização; mudanças de padrão de preenchimento entre anos podem reduzir a taxa de match em outros anos.

---

## 7. Limitação metodológica central: distrito do HOSPITAL não é distrito de RESIDÊNCIA

Esta é a limitação mais importante e precisa estar explícita em qualquer uso posterior da ponte.

O distrito que a ponte atribui a cada caso é o do ESTABELECIMENTO de internação/notificação, obtido do endereço público do hospital no CNES. Ele NÃO é o distrito onde o paciente mora. Hospitais de referência atraem pacientes de toda a cidade e de fora dela, o que distorce fortemente a distribuição espacial.

A evidência está nos próprios dados de 2024: o distrito de **BELA VISTA concentrou 22,8% (4.230) de todos os casos do ano**, não porque a maioria dos doentes resida ali, mas porque o distrito sedia grandes hospitais (por exemplo, o complexo HC-FMUSP e outras unidades de referência). Instituições como Einstein, Sabará e Santa Catarina produzem o mesmo efeito de concentração em seus respectivos distritos.

Portanto, a série temporal por distrito deve ser lida como **"carga assistencial por distrito do hospital"** e NÃO como **"incidência por local de moradia"**. São métricas diferentes, com usos diferentes.

Observação sobre alternativas nos próprios microdados: os campos `CO_MUN_RES` (município de residência) e `CS_ZONA` (zona urbana/rural/periurbana do caso) existem no SRAG, mas NÃO fornecem o distrito de residência dentro da capital. `CO_MUN_RES` só desce ao nível de município e `CS_ZONA` é uma classificação de tipo de zona, não um recorte territorial de São Paulo. Logo, não há como obter o distrito de RESIDÊNCIA a partir do open data atual.

---

## 8. Enquadramento LGPD e ISO/IEC 25012 (Confidencialidade)

A ponte foi desenhada para ser segura do ponto de vista de proteção de dados e aderente ao atributo de **Confidencialidade** da ISO/IEC 25012.

- **O recorte geográfico vem do endereço PÚBLICO do estabelecimento (CNES), nunca do paciente.** Distrito, subprefeitura, zona e bairro são todos derivados da localização do hospital, que é informação pública e cadastral. Nenhum dado de endereço, residência ou identificação do paciente é usado para o recorte espacial.
- **A saída é sempre agregada por semana epidemiológica mais distrito-do-hospital.** O artefato `saida/serie_temporal_por_distrito.csv` tem o formato `ano, semana, distrito_hospital, casos`, ou seja, apenas contagens agregadas. Nenhuma linha representa um indivíduo.
- **Nenhum dado individual identificável é produzido** em qualquer saída da ponte.
- **Resolução mais fina alcançada:** distrito > subprefeitura > zona. O bairro do hospital (campo `NO_BAIRRO` do CNES) também é público e utilizável, por ser atributo do estabelecimento e não do paciente.
- O atendimento do atributo de Confidencialidade (ISO/IEC 25012) se dá justamente porque o dado sensível de localização individual nunca entra no pipeline; só entram dados públicos de estabelecimentos e geometrias territoriais oficiais.

---

## 9. Reprodutibilidade

### Scripts e ordem de execução

1. `01_download_fontes.py`: aquisição rastreável das fontes públicas (microdados SRAG via streaming filtrado por município, recorte CNES da capital, camadas GeoSampa via WFS). Gera `dados_brutos/` e alimenta `dados_brutos/FICHA_RASTREABILIDADE.md`.
2. `02_construir_crosswalk.py`: constrói a ponte (normalização e match de nomes, lat/long, point-in-polygon contra o GeoSampa, fallback por bairro) e mede a cobertura. Gera `saida/crosswalk_unidade_distrito.csv`, `saida/serie_temporal_por_distrito.csv` e `saida/RELATORIO_COBERTURA.md`.

Ambiente: `source /projects/sandbox/_exploracao_ponte_cnes/.venv/bin/activate` (venv com pandas, requests, pdfplumber, geopandas, shapely, pyproj, pyogrio, rapidfuzz). Rodar os scripts na ordem acima.

### Fontes com datas de extração (de FICHA_RASTREABILIDADE.md)

- Microdados SRAG 2024: `https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2024/INFLUD24-23-03-2026.csv`, extração em 2026-10-01 02:36:12 UTC (267.986 linhas na origem, 18.574 retidas para a capital).
- Microdados SRAG 2013: `https://d26692udehoye.cloudfront.net/SRAG/2013-2018/INFLUD13.csv`, extração em 2026-10-01 02:36:12 UTC (36.641 na origem, 4.073 retidas; sem `NM_UN_INTE`).
- Cadastro CNES: `https://cnes.datasus.gov.br` (`cnes_estabelecimentos_csv.zip`), extração em 2026-10-01 02:36:15 UTC (637.992 na origem, 43.755 retidas para a capital).
- GeoSampa distritos: WFS `geoportal:distrito_municipal`, extração em 2026-10-01 02:36:20 UTC (96 features, EPSG:31983).
- GeoSampa subprefeituras: WFS `geoportal:subprefeitura`, extração em 2026-10-01 02:36:23 UTC (32 features, EPSG:31983).

### O que seria necessário para escala total (2009-2026)

Esta investigação processou amostras de dois anos (2024 e 2013) para provar o conceito. Para rodar em escala total:

- Iterar `01_download_fontes.py` sobre todos os anos de 2009 a 2026, usando as três famílias de URL (datasets `srag-2009-2012`, `srag-2013-2018`, `srag-2019-a-2026`).
- Manter o filtro em STREAMING por `CO_MUN_NOT=355030` (ou `ID_MUNICIP=355030` nos anos em que `CO_MUN_NOT` não existe), para não materializar os arquivos inteiros.
- **Custo de volume:** cada arquivo anual de SRAG tem cerca de 300 MB. O filtro por município em streaming é essencial: ele mantém só os casos da capital e evita baixar e armazenar ~300 MB por ano desnecessariamente. O recorte final por ano fica em poucos MB.
- Para cada ano, verificar a presença da coluna `NM_UN_INTE` antes de aplicar a ponte, pulando defensivamente os anos sem o campo (como já é feito com 2013).

---

## 10. Veredicto final

**PARCIALMENTE VIÁVEL.**

- A ponte é VIÁVEL e ROBUSTA para os anos recentes que trazem `NM_UN_INTE`: em 2024, 90,0% dos casos notificados na capital (16.722 de 18.574) foram resolvidos a um distrito, com 94,6% de match exato de nomes. A resolução chega a distrito, subprefeitura, zona e bairro, tudo a partir de dados públicos.
- A ponte NÃO é aplicável aos anos que não possuem o campo de unidade de internação (confirmado em 2013, cobertura zero). Nos primeiros anos do período do projeto (2009-2019), parte expressiva pode não ter `NM_UN_INTE`, o que precisa ser confirmado ano a ano.
- Mesmo onde funciona, o recorte representa a carga assistencial por distrito do HOSPITAL, não a incidência por local de moradia (seção 7).

Conclusão honesta: a abordagem resolve o pedido original (derivar a região intramunicipal a partir do hospital que notificou o caso) de forma sólida para os anos recentes, respeitando LGPD por usar apenas o endereço público do estabelecimento e saída sempre agregada, mas não cobre os anos antigos sem o campo de unidade e deve ser interpretada como carga por distrito do hospital.
