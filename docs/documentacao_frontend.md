# Documentacao do Frontend (Dashboard Next.js)

> Modulo **frontend** do nucleo pratico do TCC "Analise preditiva de Influenza A
> no municipio de Sao Paulo utilizando IA com dados do SIVEP-Gripe". Entrega a
> camada de visualizacao (dashboard) que consome a API REST FastAPI (pasta
> `backend/`) e sustenta os requisitos **RF001** (consulta/visualizacao de dados
> historicos) e **RF002** (exibicao de previsoes), alinhado a secao 6.5 do
> Manual Interno. Prototipo academico - nao e ferramenta oficial de vigilancia.

## 1. Visao geral

O dashboard e uma aplicacao **Next.js** (App Router) em **TypeScript**, criada em
`frontend/`. Apresenta, em uma unica tela, a serie historica semanal de
casos-proxy de Influenza A do municipio de Sao Paulo, indicadores resumidos e a
comparacao entre os valores reais e as previsoes do modelo. Toda a comunicacao
com o servidor passa por uma camada de servicos tipada que consome os seis
endpoints da API por meio da variavel `NEXT_PUBLIC_API_URL`.

O posicionamento segue a secao 2 do Manual Interno: a interface exibe, de forma
visivel, a ressalva de que se trata de um **prototipo academico** de apoio a
visualizacao e analise exploratoria, sem substituir plataformas oficiais de
vigilancia epidemiologica.

## 2. Amarração aos requisitos

| Requisito | Cobertura no frontend |
| --------- | --------------------- |
| **RF001** (consultar/visualizar dados) | Filtro por periodo (ano/semana epidemiologica, com validacao de dominio no cliente), cards de indicadores, grafico de linha (serie historica) e grafico de barras, todos consumindo `/api/dados`. |
| **RF002** (exibir previsoes de 6 semanas) | Grafico de comparacao real x previsto consumindo `/api/previsoes`, com a previsao **visualmente separada** do dado real e degradacao elegante no caso 503. |

A granularidade de consulta prevista para unidade de notificacao (`NM_UN_INTE`)
esta implementada no componente de filtro, mas tratada com honestidade porque a
fonte atual nao popula esse campo (ver secao 6). Nao ha filtro por bairro/regiao,
pois a modelagem e sempre municipal (delimitacao da secao 1.2 da documentacao do
projeto).

## 3. Escolhas técnicas

| Decisao | Justificativa |
| ------- | ------------- |
| **Next.js (App Router)** | Framework React maduro e amplamente adotado; o App Router organiza `layout`/`page` com componentes de servidor e de cliente, adequado a um dashboard interativo. Recomendacao do Manual (secao 6.5). Ver <https://nextjs.org/docs>. |
| **TypeScript** | Tipagem estatica sobre o contrato da API reduz erros de integracao; os tipos em `src/types/api.ts` espelham exatamente os schemas Pydantic do backend (`common.py`, `epidemiologia.py`). |
| **Recharts** | Biblioteca de graficos declarativa baseada em React/SVG, leve e comum, adequada aos graficos de linha, barras e comparacao real x previsto. Ver <https://recharts.org>. |
| **Estilizacao com CSS global** | Folha de estilos em `src/app/globals.css` com classes utilitarias de layout (grid responsivo, cards, filtros, estados de UI). Evita dependencia extra de framework de CSS e mantem o controle de contraste e responsividade proximo ao codigo. |
| **Camada de servicos isolada** | `src/services/api.ts` concentra o acesso HTTP: uma funcao por endpoint, desempacotamento do envelope padrao e erros tipados. Isola a UI dos detalhes de transporte. |

### 3.1 Estrutura de diretorios

```
frontend/src/
  app/         layout.tsx, page.tsx, globals.css (App Router)
  components/  Filtros, cards, graficos, estados de UI, rodape, orquestrador
  services/    api.ts (cliente HTTP), erros.ts (erros tipados), mock.ts (fallback dev)
  types/       api.ts (contrato tipado espelhando o backend)
  lib/         epidemiologia.ts (funcoes puras de formatacao/agregacao)
```

## 4. Mapeamento dashboard -> endpoints

Todas as respostas usam o envelope padrao `{ sucesso, dados, mensagem }`, que a
camada de servicos desempacota antes de entregar a UI.

| Elemento da tela | Endpoint consumido | Funcao de servico |
| ---------------- | ------------------ | ----------------- |
| Filtro de periodo -> serie historica | `GET /api/dados` (`ano_inicio`, `semana_inicio`, `ano_fim`, `semana_fim`) | `getDados()` |
| Grafico de linha (serie semanal) | `GET /api/dados` no periodo filtrado | `getDados()` |
| Grafico de barras (casos-proxy por ano epidemiologico) | `GET /api/dados` no periodo filtrado (agregado por ano) | `getDados()` |
| Cards de indicadores (total, pico, ultima semana consolidada, origem do modelo) | `GET /api/dados` (+ origem da previsao) | `getDados()` / `getPrevisoes()` |
| Grafico real x previsto | `GET /api/previsoes` (`horizonte`, padrao 6) | `getPrevisoes()` |
| Painel de metricas do modelo | `GET /api/metricas` | `getMetricas()` |
| Filtro de unidade de notificacao | `GET /api/unidades-notificacao` | `getUnidadesNotificacao()` |
| (Base) status da API/banco/modelo | `GET /api/status` | `getStatus()` |

O componente `Dashboard` (client component) mantem o estado do filtro de periodo
e refaz a consulta a `/api/dados` ao aplicar; a serie historica e as previsoes
sao buscadas em estados **independentes**, de modo que uma falha na previsao nao
derruba o restante.

## 5. Tratamento de estados e degradação elegante

Todos os componentes que buscam dados implementam tres estados explicitos,
reutilizados via `EstadoUI` (`Carregando`, `Erro`, `Vazio`):

- **Carregando:** indicador de carregamento com rotulo em Portugues-Brasil.
- **Erro:** mensagem clara, sem stack trace, com opcao de "tentar novamente".
- **Vazio:** mensagem quando a lista retorna sem registros.

O filtro por periodo ainda **valida o dominio no cliente antes de chamar a API**:
ano inteiro entre 2000 e 2100, semana epidemiologica entre 1 e 53 e coerencia
inicio <= fim (comparando ano e semana). Um valor invalido bloqueia o envio do
formulario e exibe uma mensagem clara em Portugues-Brasil (`role="alert"`), sem
delegar ao servidor um erro que a UI so mostraria de forma generica.

A **degradacao elegante** do modulo preditivo (RF002; ISO/IEC 25010 -
Confiabilidade/Tolerancia a falhas) e o ponto central: o backend isola a
indisponibilidade do preditor em **HTTP 503** (`PrevisaoIndisponivel`) sem
derrubar os endpoints de dados. No frontend, `getPrevisoes()` traduz o 503 no
erro tipado `PrevisaoIndisponivelError`, distinto de uma falha geral. Quando ele
ocorre, apenas o bloco de comparacao real x previsto e o card de origem do modelo
exibem o aviso; o grafico de linha, o grafico de barras e os cards de historico
continuam renderizando normalmente.

O card de origem do modelo **distingue** as duas situacoes, em vez de mostrar a
mesma mensagem: "Preditor indisponivel (503)" para a indisponibilidade planejada
(`PrevisaoIndisponivelError`) e "Erro ao carregar previsao" para uma falha de
comunicacao nao-503. Assim a interface preserva a diferenca entre "preditor fora
do ar por projeto" e "erro de comunicacao".

## 6. Tratamento honesto da pendência de NM_UN_INTE

O filtro de unidade de notificacao (`FiltroUnidade`) consome
`/api/unidades-notificacao`. A fonte de dados atual **nao popula** o campo
`NM_UN_INTE` (`fonte_populada = false`, `nm_un_inte = null`), o que e uma
pendencia documentada de qualidade de dados (ISO/IEC 25012 - Completude). Diante
disso, a UI:

- **nao inventa nem fabrica unidades**;
- exibe uma mensagem clara do tipo "Filtro por unidade indisponivel: a fonte de
  dados atual nao populou NM_UN_INTE (pendencia documentada)";
- mantem o seletor **desabilitado** enquanto a fonte nao trouxer unidades reais.

Importante: mesmo no cenario futuro em que a fonte popule `NM_UN_INTE`
(`fonte_populada = true`), o seletor passa a **listar** as unidades reais por
transparencia, mas continua **desabilitado**, com nota de "em breve". Isso evita
apresentar um controle que aparenta filtrar sem filtrar, ja que a API ainda nao
expoe um parametro de filtro por unidade em `/api/dados`. O seletor so sera
habilitado (com o estado selecionado sendo levado a consulta) quando o backend
oferecer esse parametro.

## 7. Separação visual real x previsto

Conforme a secao 6.5 do Manual (erro a evitar: misturar visualmente previsao e
real), o grafico de comparacao mantem as series em campos distintos:

- **Real:** linha continua.
- **Previsto:** linha tracejada em cor distinta, com legenda propria e uma
  linha/marcador de referencia indicando o inicio da previsao.

Uma ancora liga a ultima observacao real ao inicio do previsto sem sobrepor
valores, e a origem do modelo (`modelo_treinado` ou `baseline`) e o nome do
modelo sao exibidos quando disponiveis. Alem disso, as **8 semanas mais recentes**
reservadas por atraso de notificacao (`reservada_atraso_notificacao = true`, que
nao entram no treino) sao sinalizadas visualmente no grafico de linha (area
sombreada/marcador distinto) com nota explicativa. Todos os graficos possuem
titulo, indicacao de periodo e legenda.

## 8. Responsividade e acessibilidade

- **Responsividade:** layout em grade que colapsa em telas estreitas; os graficos
  usam container responsivo do Recharts. Testado nas larguras mobile e desktop
  via CSS (`globals.css`).
- **Acessibilidade basica:** rotulos associados aos controles de filtro
  (`htmlFor`/`id`), `aria-describedby` no aviso da pendencia de unidade,
  `role="status"`/`role="alert"` nos estados de carregamento/erro, `aria-label`
  nas secoes de grafico e respeito a `prefers-reduced-motion` (desativa a
  animacao do indicador de carregamento). O contraste das cores foi considerado
  na folha de estilos.

## 9. Posicionamento como protótipo acadêmico

A ressalva academica fica visivel no rodape (componente `AvisoPrototipo`,
reutilizado do scaffold) em todas as telas: "Prototipo academico (TCC). Nao e
ferramenta oficial de vigilancia epidemiologica. Fonte: SIVEP-Gripe/DATASUS".
Quando o modo mock de desenvolvimento esta ativo (`NEXT_PUBLIC_USAR_MOCK=true`),
um aviso adicional deixa claro que os dados sao ficticios e que a versao final
consome a API real.

## 10. Configuração e execução

Instrucoes operacionais (instalar, configurar `NEXT_PUBLIC_API_URL`, rodar em
desenvolvimento e producao, e subir o backend para integracao) estao em
[`../frontend/README.md`](../frontend/README.md). Em resumo: `npm install`,
copiar `.env.example` para `.env.local`, `npm run dev` (desenvolvimento) ou
`npm run build && npm run start` (producao); para integracao real, subir o
backend com `cd backend && uv sync && uv run uvicorn app.main:app --reload`.

## 11. Validação nesta entrega

A validacao do frontend nesta fase e feita por **lint** e **build** (nao ha
suite de testes unitarios exigida para o frontend na secao 6.5 do Manual):

```bash
cd frontend && npm run lint && npm run build
```

Ambos concluem sem erros: o ESLint do Next reporta "No ESLint warnings or errors"
e o `next build` compila sem erros de tipo, gerando a rota do dashboard. A
integracao ponta a ponta com dados reais depende de um banco populado; no
ambiente de desenvolvimento sem dados, a camada de servicos aponta corretamente
ao contrato real e os estados de carregamento/erro/vazio permanecem exercitaveis.

## 12. Rastreabilidade de referências

Cada decisao de projeto do frontend foi ancorada nos documentos-fonte do TCC e em
documentacoes tecnicas publicas.

| Conteudo aplicado no frontend | Fonte utilizada | Localizacao / link |
| ----------------------------- | --------------- | ------------------ |
| Requisitos RF001/RF002; dashboard, filtros, cards, graficos e comparacao real x previsto | TCC - C D H M (TC2), secoes de requisitos funcionais | `Documentos_Para_Desenv_TCC/TCC - C D H M (TC2).docx` |
| Entregaveis em `src/components`/`src/services`; filtros por periodo e unidade; graficos com titulo/periodo/legenda; previsao separada do real; loading/erro; responsividade; posicionamento de prototipo | Manual Interno de Desenvolvimento (secoes 2 e 6.5) | `Documentos_Para_Desenv_TCC/Manual_Interno_Desenvolvimento_TCC_Influenza_v2.docx` |
| Contrato da API (envelope, endpoints, 503 do preditor) e pendencia de NM_UN_INTE | Documentacao do backend | [`documentacao_backend.md`](documentacao_backend.md) |
| Delimitacoes (escopo municipal; sem filtro por bairro/regiao; 8 semanas reservadas) e qualidade de dados | Documentacao consolidada do projeto e relatorio de qualidade | [`documentacao_projeto.md`](documentacao_projeto.md), [`relatorio_qualidade_dados.md`](relatorio_qualidade_dados.md) |
| Tolerancia a falhas (degradacao elegante do preditor) | Anexo de Qualidade ISO/IEC 25000 v4 (ISO/IEC 25010 - Confiabilidade) | `Documentos_Para_Desenv_TCC/TCC_Anexo_Qualidade_ISO_IEC_25000_v4.docx` |
| Next.js (App Router, `layout`/`page`, componentes de cliente) | Documentacao oficial do Next.js | https://nextjs.org/docs |
| Recharts (graficos de linha, barras e composicao) | Documentacao oficial do Recharts | https://recharts.org |
| React (componentes, estado, hooks) | Documentacao oficial do React | https://react.dev/ |
| TypeScript (tipagem do contrato) | Documentacao oficial do TypeScript | https://www.typescriptlang.org/docs/ |
| Semana epidemiologica (conceito) | Ministerio da Saude / SIVEP-Gripe (DATASUS) | https://opendatasus.saude.gov.br/ |

> Uso de IA no desenvolvimento seguindo as normas do CNPq (documento
> `Documentos_Para_Desenv_TCC/Normas CNPQ Uso de IA.pdf`).
