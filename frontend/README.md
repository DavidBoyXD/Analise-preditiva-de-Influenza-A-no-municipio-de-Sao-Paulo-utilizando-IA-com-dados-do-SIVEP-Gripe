# Frontend - Dashboard de Influenza A (Municipio de Sao Paulo)

Protótipo academico (TCC) de analise preditiva de Influenza A, construido em
Next.js (App Router) + TypeScript. Consome a API REST FastAPI do mesmo
repositorio (pasta `backend/`).

> Ressalva: aplicacao de finalidade exclusivamente educacional e de pesquisa.
> Nao e ferramenta oficial de vigilancia epidemiologica.

## Requisitos

- Node.js 18+ (validado com Node 22) e npm.

## Configuracao

1. Instale as dependencias:
   ```bash
   npm install
   ```
2. Copie o arquivo de variaveis de ambiente e ajuste conforme o ambiente:
   ```bash
   cp .env.example .env.local
   ```
   - `NEXT_PUBLIC_API_URL`: URL base da API FastAPI (padrao `http://localhost:8000`).
     O prefixo `/api` e adicionado automaticamente pela camada de servicos.
   - `NEXT_PUBLIC_USAR_MOCK`: `true` apenas para desenvolver a UI sem backend.
     O caminho padrao e sempre a API real.

## Scripts

- `npm run dev` - servidor de desenvolvimento (padrao em `http://localhost:3000`).
- `npm run build` - build de producao.
- `npm run start` - executa o build de producao (rode `npm run build` antes).
- `npm run lint` - ESLint (configuracao do Next).

### Desenvolvimento

```bash
npm install
cp .env.example .env.local   # ajuste NEXT_PUBLIC_API_URL se necessario
npm run dev
```

### Build e producao

```bash
npm run build
npm run start
```

## Integracao com o backend

O dashboard consome a API REST FastAPI do mesmo repositorio (pasta `backend/`).
Para rodar a integracao ponta a ponta, suba o backend em outro terminal e aponte
`NEXT_PUBLIC_API_URL` para ele:

```bash
# a partir da raiz do repositorio
cd backend
uv sync
uv run uvicorn app.main:app --reload   # sobe a API em http://localhost:8000
```

Com o backend no ar e `NEXT_PUBLIC_API_URL=http://localhost:8000` no
`.env.local`, o `npm run dev` do frontend carrega o dashboard consumindo os
endpoints reais (`/api/status`, `/api/dados`, `/api/series-temporais`,
`/api/previsoes`, `/api/metricas`, `/api/unidades-notificacao`). A documentacao
tecnica completa do dashboard esta em
[`../docs/documentacao_frontend.md`](../docs/documentacao_frontend.md).

## Estrutura

```
src/
  app/         Paginas e layout (App Router)
  components/  Componentes de UI reutilizaveis
  services/    Cliente HTTP tipado da API (api.ts), erros e mock de dev
  types/       Tipos TypeScript que espelham o contrato da API
```

## Decisoes tecnicas

- **Biblioteca de graficos: Recharts.** Leve, popular e declarativa (baseada em
  React/SVG), adequada para os graficos de linha, barras e comparacao real x
  previsto do dashboard. Instalada nesta etapa para uso na etapa seguinte.
- **Camada de servicos (`src/services/api.ts`):** uma funcao por endpoint,
  desempacotando o envelope padrao `{ sucesso, dados, mensagem }` da API. Erros
  sao tipados (`ErroApi`) para a UI distinguir os casos. O HTTP 503 de
  `/api/previsoes` vira um estado especifico (`PrevisaoIndisponivelError`),
  permitindo degradacao elegante (o historico continua visivel mesmo quando a
  previsao falha).
- **Tipos (`src/types/api.ts`):** espelham exatamente os schemas Pydantic do
  backend (`backend/app/schemas/common.py` e `epidemiologia.py`).
- **Mock (`src/services/mock.ts`):** apenas fallback de desenvolvimento,
  ativado por `NEXT_PUBLIC_USAR_MOCK=true`. Nunca e o caminho padrao.

## Idioma

Interface e textos em Portugues-Brasil. O codigo usa ingles apenas onde e
convencao tecnica (nomes de libs, props de framework).
