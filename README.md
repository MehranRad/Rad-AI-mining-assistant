# Rad AI — Mining Intelligence Assistant

A locally-hosted LLM-powered assistant for querying copper mining operations data in natural language (Persian/Farsi) — with role-based access control, layered security, conversation memory, and fully offline inference.

> Originally built as an internship prototype, this project evolved into a full-stack application: a Next.js frontend, a FastAPI backend, and local LLM inference via Ollama — with no data ever leaving the local network.

---

## Features

- **Natural-language querying in Persian** over production, equipment, and workforce data
- **Fully offline / local inference** — no cloud LLM APIs, powered by [Ollama](https://ollama.com)
- **Role-based access control (RBAC)** — three access tiers (staff, supervisor, manager) with different data-visibility rules
- **Layered security pipeline** — semantic intent classification, pattern-based filtering, and generated-SQL inspection before any query touches the database
- **Prompt-injection and schema-probing resistant**
- **Conversation memory** — resolves follow-up questions and corrections across the last few turns without the user repeating context
- **Streaming responses** — answers render token-by-token over Server-Sent Events
- **JWT-based authentication** — role and identity are derived from a signed token, never trusted from client input
- **Audit logging** — tracks question categories and access decisions without persisting sensitive content unnecessarily
- **Persian-first UI** with full RTL support, built with Next.js, TypeScript, and Tailwind CSS

---

## Architecture

┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Next.js (RTL) │─────▶│ FastAPI backend │─────▶│ Ollama (local) │
│ TypeScript │ JWT │ RBAC + security │ │ LLM inference │
│ Tailwind CSS │◀─────│ layer + agent │◀─────│ │
└─────────────────┘ └────────┬─────────┘ └─────────────────┘
│
▼
┌──────────────────┐
│ MySQL (local) │
│ Production/Equip- │
│ ment/Employees │
└──────────────────┘


An earlier, simpler version of this project — a single-process Streamlit application — is preserved on the `main` branch for reference. Active development now lives on `nextjs-frontend`.

### Query pipeline

1. **Follow-up resolution** — rewrites a question that depends on prior conversation context (a correction, a pronoun reference) into a self-contained question.
2. **Security classification** — every question is checked against categories such as individual-personal-data requests, prompt injection, schema probing, and bulk extraction, before any SQL is generated.
3. **Routing** — simple factual questions go through a single dynamically-generated, validated SQL query; broader analytical questions (comparisons, "why" questions) run a set of pre-defined, safe aggregate queries across multiple tables.
4. **Computation in Python, not the LLM** — all numeric comparisons, rankings, and derived metrics are computed in Python and handed to the model as pre-verified facts, to minimize numerical hallucination.
5. **Answer synthesis** — the LLM turns the retrieved, precomputed data into a concise Persian answer, streamed back to the client.

---

## Tech stack

**Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Framer Motion, Three.js (`@react-three/fiber`)
**Backend:** FastAPI, LangChain (SQLDatabase utilities), PyJWT
**LLM inference:** Ollama, running Qwen-family models locally
**Database:** MySQL (local instance)

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed locally, with a model pulled (e.g. `ollama pull qwen3:4b-instruct-2507-q4_K_M`)
- A local MySQL server

### Backend setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env           # fill in your local DB credentials and a JWT secret

python load_data.py            # loads the sample dataset into MySQL
uvicorn api_server:app --reload --port 8000
```

### Frontend setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## Project structure

.
├── agent.py # Core LLM pipeline: routing, security, SQL generation, answer synthesis
├── api_server.py # FastAPI app exposing agent.py over HTTP, with JWT auth
├── chat_storage.py # Conversation history, users, and audit log persistence
├── load_data.py # Loads and cleans the sample dataset into MySQL
├── frontend/ # Next.js application
│ ├── app/ # Pages (login, chat)
│ ├── components/ # UI components (chat, sidebar, auth, 3D visuals)
│ └── lib/ # API client, types
└── data/ # Sample synthetic dataset (Employees, Equipment, Production)


---

## Notes

- The dataset included in this repository is **synthetic** — generated to resemble realistic mining company data, not real company records.
- Persian text is stored and queried in its original form throughout the pipeline; the LLM is instructed never to transliterate or translate categorical values.
- This project is a personal/portfolio project and is not affiliated with any specific mining company.

---

## License

This project is currently unlicensed for reuse. All rights reserved unless a license file is added.
