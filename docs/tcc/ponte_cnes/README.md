# Ponte CNES → distrito: relatórios-fonte (análise exploratória)

Esta pasta reúne os relatórios que embasam os números da **análise exploratória
complementar** descrita no documento de TCC (`../TCC_Influenza_A_SP_v1.md`,
seções 4.9 e 5.3): o recorte intramunicipal por distrito de São Paulo derivado
do hospital notificante (campo `NM_UN_INTE` do SRAG) via cadastro público CNES e
camadas territoriais do GeoSampa.

> **Natureza do material.** Os relatórios abaixo foram produzidos em uma
> investigação **exploratória e isolada**, conduzida fora do fluxo principal do
> projeto, apenas com **fontes públicas** (microdados SRAG do openDATASUS,
> cadastro CNES do DATASUS e camadas do GeoSampa/Prefeitura de São Paulo), com
> extração datada de outubro de 2026. São versionados aqui para dar
> **rastreabilidade** aos números citados no documento de TCC. A ponte é uma
> **prova de conceito validada apenas no ano de 2024** (90,0% dos casos da
> capital resolvidos a um distrito) e carrega a limitação central de que o
> distrito identificado é o do **hospital**, não o da **residência** do paciente.

## Conteúdo

| Arquivo | Descrição |
| ------- | --------- |
| [`RELATORIO_VIABILIDADE_PONTE.md`](RELATORIO_VIABILIDADE_PONTE.md) | Relatório completo de viabilidade: disponibilidade das fontes, método (3 saltos), cobertura, limitações, enquadramento LGPD/ISO 25012 e reprodutibilidade. |
| [`RELATORIO_COBERTURA.md`](RELATORIO_COBERTURA.md) | Métricas de cobertura por ano (2024 aplicável, 2013 não aplicável) e os 15 distritos com mais casos em 2024. |
| [`FICHA_RASTREABILIDADE_FONTES.md`](FICHA_RASTREABILIDADE_FONTES.md) | Procedência auditável de cada fonte pública: URL, data/hora de extração, volume e colunas. |

## Observações importantes

- **Proteção de dados (LGPD / ISO/IEC 25012, Confidencialidade):** o recorte
  geográfico vem exclusivamente do endereço **público do hospital** (CNES),
  nunca do paciente. A saída é sempre agregada por semana epidemiológica mais
  distrito-do-hospital; nenhum dado individual identificável é produzido.
- **Interpretação:** a série por distrito representa **carga assistencial por
  distrito do hospital**, e não incidência por local de moradia. Hospitais de
  referência concentram casos (ex.: Bela Vista, 22,8% em 2024, por sediar
  grandes unidades).
- **Aplicabilidade parcial:** anos sem o campo `NM_UN_INTE` (confirmado em 2013)
  não são cobertos; a presença do campo deve ser confirmada ano a ano para o
  período 2009–2019.
- Os scripts reprodutíveis que geraram estes relatórios permanecem na área de
  investigação isolada (fora do repositório); esta pasta preserva os relatórios
  de saída para fins de rastreabilidade documental.
