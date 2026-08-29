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
