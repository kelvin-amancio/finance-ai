# 💰 Finance AI — Agente Financeiro no WhatsApp

Um agente financeiro pessoal que vive dentro do **WhatsApp**. Você conversa como
com qualquer contato — manda texto, um **áudio** ou um **print** do banco/nota — e ele
entende, categoriza e registra tudo. Depois é só perguntar quanto gastou, pedir dicas
ou exportar um relatório.

Inspirado na experiência do [Pierre](https://lp.pierre.finance), mas 100% via WhatsApp.
É **multi-usuário**: cada número que entra com o código de convite tem o seu próprio
gestor (gastos, limites e resumos independentes).

---

## ✨ Funcionalidades

- Registro de gastos/receitas por **texto**, **áudio** e **print/imagem**
- **Parcelas que abatem mês a mês** e **assinaturas recorrentes** (contas fixas)
- **Limites mensais** por categoria, com avisos de estouro
- **Listar, editar e remover** gastos por nome, número da lista ou categoria
- **Relatórios** em Excel (.xlsx) e PDF (com gráficos)
- **Resumos automáticos** semanal e mensal
- **Multi-usuário** com código de convite
- **IA em cascata** com fallback entre provedores + **OCR/transcrição local** (funciona sem internet)

---

## 🗣️ Como usar (exemplos)

| Você manda | O agente faz |
|---|---|
| "gastei 25 no almoço" | Registra e mostra o total do mês (+ avisa se atingir um limite) |
| "comprei 1800 em 12x" | Registra **parcelado** (12x de R$150, total R$1.800) |
| "recebi 3000 de salário" | Registra como **receita** |
| "resumo da semana" | Mostra total e divisão por categoria |
| "onde posso economizar?" | Dá dicas práticas com base nos maiores gastos e limites |
| "definir limite de mercado 500" | Cria/atualiza um **limite mensal** |
| "quais minhas assinaturas?" | **Lista** os gastos da categoria |
| "edita a netflix para 49" / "editar o 2 para 50" | **Edita** um gasto |
| "remove a netflix" / "remover o item 1 de contas fixas" | **Remove** um gasto |
| "me manda um excel" / "quero um pdf" | Envia o **relatório** |
| 📷 mandar um **print** | Lê, mostra um **rascunho** e pergunta se pode salvar |
| 🎤 mandar um **áudio** | Transcreve e registra normal |

---

## 🎤 Áudio e 🖼️ Prints

- **Áudio:** transcrito e processado como se você tivesse digitado.
- **Print/imagem:** é interpretado e vem como **rascunho** para você confirmar:
  `salvar` grava · `editar 2 para 50` / `remover 3` ajustam · `cancelar` descarta.
  Um comprovante vira **uma** despesa com o valor total; uma lista de transações vira
  **uma por linha** (detecta receita vs despesa em extratos).

## 🔢 Parcelas e recorrentes

- **Parcelado** (ex.: `7/12`, `12x`): guarda valor da parcela, total e progresso.
  Um job mensal **abate 1 parcela por mês** e encerra o gasto no fim.
- **Recorrente** (assinaturas/contas fixas): entra **todo mês**.
- O resumo mensal soma: único (no mês), recorrente (todo mês) e parcelado (enquanto ativo).

---

## 🏗️ Arquitetura

```
 WhatsApp (usuário)
        │  mensagem recebida
        ▼
 Evolution API  ──(webhook)──►  n8n
 (WhatsApp)                      │
                                 ├─ IA (classifica intenção + escreve a resposta)
                                 ├─ PostgreSQL (gastos, limites, usuários)
                                 ├─ Redis (dedup / rascunho / cache)
                                 └─ serviços auxiliares (PDF e mídia local)
        ◄───────────────────────  Evolution (sendText / sendMedia)
 WhatsApp (resposta)
```

A IA é usada em **apenas 2 pontos**: **classificar** a mensagem (JSON estruturado) e
**formatar** a resposta. **Todo cálculo e persistência é determinístico** — a IA nunca
faz conta nem escreve no banco.

### Stack

| Camada | Tecnologia |
|---|---|
| Orquestração | **n8n** |
| WhatsApp | **Evolution API** (Baileys) |
| Banco | **PostgreSQL** |
| Cache/estado | **Redis** |
| LLM (cascata) | Groq → Gemini → OpenRouter → **Ollama** (local) |
| Áudio | Whisper (nuvem) + **Vosk** (local) |
| Imagem/OCR | Gemini Vision (nuvem) + **Tesseract** (local) |
| Relatórios | PDF (Node/PDFKit) e Excel (nó nativo do n8n) |
| Infra | **Docker / Docker Compose** |

---

## 🚀 Como rodar

Pré-requisitos: Docker, uma instância do **Evolution API** conectada a um número de
WhatsApp, um **n8n** e um **PostgreSQL**/**Redis** (podem ser os do seu stack).

1. **Banco:** aplique `db/schema.sql` e as migrações em `db/` no seu PostgreSQL.
2. **Serviços auxiliares:** `docker compose up -d --build` (sobe o gerador de PDF e o
   serviço local de mídia, na mesma rede do n8n).
3. **n8n:** importe `n8n/workflow.json` e crie as credenciais:
   - `Postgres`, `Redis`
   - `Groq` (e, opcionalmente, `Gemini`, `OpenRouter`, `Ollama`) para a cascata de IA
4. **Variáveis de ambiente do n8n:** defina as chaves dos provedores de IA e a
   `EVOLUTION_API_KEY` (usadas via `$env` nos nós). Ex.: `GROQ_API_KEY`, `GEMINI_API_KEY`,
   `OPENROUTER_API_KEY`, `EVOLUTION_API_KEY`, além de `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
5. **Webhook:** aponte a instância do Evolution (evento `MESSAGES_UPSERT`) para o webhook
   do workflow.
6. **Ative** os workflows no n8n.

> Os workflows já vêm com **fallback**: se um provedor de IA cair, o próximo assume;
> e para mídia há um serviço local (OCR/transcrição) sem custo por uso.

---

## ⚙️ Personalização

- **Provedores/modelos de IA:** nos nós de modelo e nas cadeias de classificação/formação.
- **Categorias:** tabela `categorias`.
- **Persona e tom:** nos prompts dos nós de classificação e de resposta.
- **Horários dos resumos:** nos nós de agendamento.

---

## 🧩 Nota técnica: LID do WhatsApp

O WhatsApp moderno identifica usuários por **LID** (`…@lid`), não pelo telefone. O agente
separa os dois papéis: usa o **telefone** para identidade no banco e o **LID** para
**entregar as respostas** (responder ao telefone faz a mensagem ficar “aguardando”).
O identificador de envio é atualizado a cada mensagem.

---

## 📄 Licença

MIT — veja [LICENSE](./LICENSE).
