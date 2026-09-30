# Plano de Segurança

> Documento de segurança do TCC "Análise preditiva de Influenza A no município de
> São Paulo utilizando IA com dados do SIVEP-Gripe", conforme a seção 6.8 do
> Manual Interno e a ISO/IEC 27002:2022 (usada como boas práticas de referência,
> **não** como declaração de conformidade formal — desproporcional a um protótipo
> acadêmico). Protótipo acadêmico.

## 1. Escopo

Cobre proteção de credenciais, CORS, controle de acesso administrativo, logs,
backup e privacidade/LGPD, distinguindo o que já está **implementado** no núcleo
prático do que é **planejado** para a fase de nuvem/frontend.

## 2. Proteção de credenciais (implementado)

- Nenhuma credencial fica embutida no código-fonte.
- A string de conexão vem da variável de ambiente `DATABASE_URL`.
- `.env.example` (raiz) documenta as variáveis **sem segredos reais**; o `.env`
  está no `.gitignore`.
- Base ISO/IEC 27002: **8.24 (uso de criptografia / proteção de segredos)** e
  segregação de configuração.

## 3. CORS (implementado / configurável)

- Origens permitidas configuráveis por `CORS_ORIGENS`. Em produção, restringir à
  origem do frontend (não usar `*`).
- Implementado no `app/main.py` via middleware do FastAPI.

## 4. Controle de acesso administrativo (planejado)

- Diferenciar o acesso do **usuário comum** (leitura pública dos dados) do acesso
  da **equipe técnica** (operações administrativas).
- Rotas administrativas, quando implementadas, devem exigir autenticação com
  mecanismo padrão (ex.: JWT), **não** implementação caseira.
- Base ISO/IEC 27002: **5.15 (controle de acesso)**, **8.2/8.3 (acesso
  privilegiado/restrição de acesso)**, **8.5 (autenticação segura)**.
- Status: **pendente** — o núcleo prático atual expõe apenas consultas de leitura.

## 5. Logs e auditoria (implementado)

- Logs estruturados da API (timestamp, nível, origem, mensagem) e do middleware de
  requisição (método, rota, status, duração).
- Tabela `log_processamento` registra eventos de processamento (com stack trace),
  e `fonte_dados`/`arquivo_dados` tornam cada escrita atribuível a uma origem.
- Base ISO/IEC 27002: **8.15/8.16 (registro de eventos e monitoramento)**; ISO/IEC
  25010 — Manutenibilidade (Analisabilidade); ISO/IEC 25012 — Rastreabilidade.
- Logs de infraestrutura em nuvem: **planejados** (ver `docs/plano_nuvem.md`).

## 6. Criptografia e transporte (planejado)

- HTTPS em toda a comunicação com a API e criptografia em repouso no RDS/S3.
- Base ISO/IEC 27002: **8.24**. Status: **pendente de confirmação** (fase de nuvem).

## 7. Backup (planejado / parcial)

- RDS com backup automático nativo; retenção e teste de restore a documentar.
- S3 com versionamento; base bruta nunca sobrescrita.
- Base ISO/IEC 27002: **8.13 (cópia de segurança)**.

## 8. Gestão de vulnerabilidades e mudanças (planejado)

- Verificação automática de dependências (ex.: Dependabot) para Python e
  JavaScript — ISO/IEC 27002 **8.8**.
- Troca do modelo `.joblib` em produção segue convenção de versão + registro da
  versão ativa — ISO/IEC 27002 **8.32**.

## 9. Privacidade e LGPD

- O sistema usa **exclusivamente dados agregados** por semana epidemiológica e
  localidade (município). Não há exposição de campos sensíveis individuais
  (idade, raça/cor etc.) pela API — princípio de **minimização de dados** da LGPD
  (Lei nº 13.709/2018). Base ISO/IEC 25012 — Conformidade/Confidencialidade.
- **Ressalva sobre `NM_UN_INTE`:** o campo de unidade de notificação **identifica
  um hospital/unidade de saúde**. Caso a fonte passe a populá-lo e o dashboard o
  exponha, o cruzamento de unidade + período em recortes de baixa contagem pode
  reduzir o anonimato. Recomenda-se: manter agregação semanal, suprimir/mascarar
  contagens muito pequenas por unidade e restringir a exposição do campo conforme
  a política de acesso. A ausência de bairro no SIVEP-Gripe/SINAN já reforça a
  minimização. Status: o campo **não é populado** pela fonte atual (pendência
  documentada), então o risco é potencial e tratado por precaução.
- Nenhuma decisão automática de saúde pública é tomada pelo sistema; as previsões
  são somente leitura e exploratórias (ISO/IEC 25059 — Segurança Operacional /
  Restrição operacional).

## 10. Referências

Ver a seção de referências ABNT (NBR 6023) em
[`docs/documentacao_projeto.md`](documentacao_projeto.md), seção 8.
