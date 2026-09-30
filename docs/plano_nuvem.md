# Plano de Nuvem

> Documento de planejamento de nuvem do TCC "Análise preditiva de Influenza A no
> município de São Paulo utilizando IA com dados do SIVEP-Gripe", conforme a
> seção 6.8 do Manual Interno. **Importante:** a infraestrutura de nuvem descrita
> aqui é **planejamento documentado**, **não provisionado** neste ambiente. Não há
> acesso a AWS (EC2/RDS/S3) durante o desenvolvimento do núcleo prático; a
> validação do banco foi feita via container Docker (PostgreSQL 16) e via SQLite.
> Protótipo acadêmico.

## 1. Objetivo

Descrever como o sistema seria implantado em nuvem (AWS) na fase seguinte, tratando
computação, banco, armazenamento, backup, custos estimados e limites do ambiente
acadêmico — evitando tratar a nuvem apenas como hospedagem genérica (erro apontado
no Manual, seção 6.8).

## 2. Topologia planejada (AWS)

| Serviço | Uso | Componente do sistema |
| ------- | --- | --------------------- |
| **Amazon EC2** | Instância que hospeda o backend FastAPI (uvicorn) e serve o modelo `.joblib` em memória. | Backend / modelo |
| **Amazon RDS (PostgreSQL)** | Banco relacional gerenciado, com backup automático. | Banco de dados |
| **Amazon S3** | Armazenamento de objetos: base bruta preservada, artefatos tratados e modelos versionados. | Armazenamento / backup |
| **Frontend (Next.js)** | Hospedagem estática/SSR (ex.: Vercel ou S3+CloudFront) na fase futura. | Frontend |

## 3. Fluxo de implantação previsto

1. Provisionar RDS PostgreSQL e aplicar `database/schema.sql`, `indexes.sql` e
   `seed.sql`.
2. Subir a instância EC2, configurar as variáveis de ambiente (`.env`, com
   `DATABASE_URL` apontando para o RDS) e iniciar a API com uvicorn.
3. Publicar os artefatos (`data/`, `models/`) e cópias de backup no S3.
4. Publicar o frontend Next.js apontando para a URL pública da API (CORS restrito
   à origem do frontend).

## 4. Backup e recuperação

- **RDS:** backup automático nativo (snapshots diários) com retenção a definir;
  restore testado periodicamente (ISO/IEC 27002 8.13; ISO/IEC 25010 — Capacidade
  de recuperação).
- **S3:** versionamento de objetos habilitado; a **base bruta original nunca é
  sobrescrita** (regra do Manual, seção 6.2), preservada como cópia fiel.
- **Modelo:** versionamento por nome de arquivo (`modelo_rf_v1.joblib`) e registro
  da versão ativa na tabela `modelo_preditivo` (ISO/IEC 27002 8.32).

## 5. Custos estimados e limites acadêmicos

Estimativa **de ordem de grandeza** para um protótipo acadêmico de baixo tráfego
(sujeita a variação por região e câmbio; não é cotação):

| Item | Configuração de referência | Faixa mensal estimada (USD) |
| ---- | -------------------------- | --------------------------- |
| EC2 | Instância pequena (ex.: t3.small), uso intermitente | ~15–30 |
| RDS PostgreSQL | Instância pequena (ex.: db.t3.micro) + armazenamento | ~15–30 |
| S3 | Poucos GB + versionamento | ~1–5 |
| Transferência de dados | Baixo volume | ~1–5 |

**Limites do ambiente acadêmico:**

- Preferir a camada gratuita (AWS Free Tier) quando aplicável e desligar recursos
  fora dos períodos de demonstração para conter custos.
- O sistema é um protótipo de baixo tráfego; não há requisito de alta
  disponibilidade. Meta de uptime **provisória** de ≥ 95% em ambiente de teste
  (ISO/IEC 25010 — Disponibilidade), sem SLA formal.
- Escalabilidade tratada como planejamento: o banco em 3FN e a camada de acesso
  portável suportam aumento de volume sem redesenho (ISO/IEC 25010 —
  Escalabilidade), mas testes de carga ficam para a fase de implantação.

## 6. Monitoramento (planejado)

- Logs de aplicação já produzidos pela API e por `log_processamento` no banco.
- Logs de infraestrutura (ex.: CloudTrail) e ferramenta de monitoramento a definir
  na fase de implantação (ISO/IEC 27002 8.15/8.16).

## 7. Segurança em nuvem

Os controles de segurança (CORS, acesso administrativo, criptografia, credenciais)
estão detalhados em [`docs/plano_seguranca.md`](plano_seguranca.md).

## 8. Referências

Ver a seção de referências ABNT (NBR 6023) em
[`docs/documentacao_projeto.md`](documentacao_projeto.md), seção 8.
