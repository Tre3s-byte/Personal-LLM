<p align="center">
  <h1 align="center">Personal AI Server</h1>
  <p align="center">
    Self Hosted · Local LLM · RAG Engine · Remote Access Ready
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LLM-Local-blue" />
  <img src="https://img.shields.io/badge/RAG-FAISS-green" />
  <img src="https://img.shields.io/badge/API-FastAPI-purple" />
  <img src="https://img.shields.io/badge/Access-VPN-orange" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" />
</p>

---

## Overview

**Personal self hosted AI infrastructure** designed to run locally, accessible remotely through a secure private network, and structured for future multi user expansion.

> **This project is not a chatbot.**  
> It is an AI operating layer for a personal workstation.

---

# Vision

## AI Server provides

- Local LLM inference
- Retrieval Augmented Generation over personal documents
- Secure file access
- Remote API access from phone
- Controlled system automation
- Wake on LAN integration
- Future multi user readiness

**Goal:** full ownership, privacy, extensibility.

---

# Core Features

## 1. Local LLM Layer

- Runs fully offline
- GPU optional
- Model interchangeable
- Wrapped behind a service interface

---

## 2. RAG Engine

- Local embeddings
- FAISS vector store
- Document ingestion pipeline
- Context injection before generation

---

## 3. File Access Layer

- Whitelisted directories only
- List files
- Search files
- Read and summarize documents
- Secure file download endpoint

---

## 4. System Automation Layer

- Controlled shutdown
- Restart
- Wake on LAN
- Predefined safe scripts only
- No arbitrary command execution

---

## 5. Secure API

- JWT authentication
- Role based structure ready
- Multi user compatible architecture

---

## 6. Remote Access

- Designed for VPN usage, Tailscale recommended
- No public port exposure required

---

# High Level Architecture

```
Phone
   ↓
VPN (Tailscale)
   ↓
FastAPI Backend
   ↓
Service Layer
   ↓
LLM + Vector Store + Filesystem
```

Each layer is isolated and replaceable.

---

# Project Structure

```
ai-server/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── chat.py
│   │   ├── files.py
│   │   ├── system.py
│   │   └── auth.py
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   ├── embedding_service.py
│   │   ├── file_service.py
│   │   └── system_service.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── models/
│   │   └── schemas.py
│
├── data/
│   ├── vector_store/
│   └── documents/
│
├── scripts/
│   ├── ingest.py
│   └── wake_pc.py
│
├── requirements.txt
└── README.md
```

---

# Design Principles

- Separation of concerns
- Service oriented architecture
- No direct filesystem exposure
- Authentication required for every endpoint
- All system actions validated and restricted
- Multi user ready from day one

---

# Installation

## 1. Clone Repository

```bash
git clone <repo_url>
cd ai-server
```

## 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Run Server

```bash
uvicorn app.main:app --reload
```

API documentation:

```
http://127.0.0.1:8000/docs
```

---

# LLM Configuration

Location:

```
app/services/llm_service.py
```

### Supported Backends

| Backend      | Purpose                |
| ------------ | ---------------------- |
| Ollama       | Recommended production |
| Transformers | Full local control     |
| llama.cpp    | Lightweight inference  |

Model can be swapped without changing the API layer.

---

# RAG Workflow

```
Documents → Embeddings → FAISS Index → Similarity Search → Context Injection → LLM Response
```

Steps:

1. Documents placed in `data/documents`
2. Ingestion script generates embeddings
3. FAISS index stored in `data/vector_store`
4. Query triggers similarity search
5. Context injected into prompt
6. LLM generates answer

The RAG layer has no knowledge of HTTP or authentication.

---

# File System Security

Only whitelisted directories are accessible.

Configured in `config.py`:

```python
ALLOWED_PATHS = [
    "C:/Users/username/Documents",
    "C:/Users/username/Projects"
]
```

All file operations validated against this list.

---

# System Automation Rules

Only predefined actions are executable.

```python
ALLOWED_ACTIONS = {
    "shutdown": shutdown_pc,
    "restart": restart_pc,
    "backup": run_backup
}
```

No arbitrary shell execution allowed.

---

# Remote Access Setup

## Recommended: Tailscale VPN

1. Install Tailscale on PC
2. Install Tailscale on phone
3. Connect both to same network
4. Access API via Tailscale IP

No router port forwarding required.

---

# Wake on LAN Setup

### Requirements

- BIOS Wake on LAN enabled
- Network adapter configured
- Secondary device always online or router support

### Optional Architecture

```
Phone → Always On Device → Magic Packet → PC Boots → AI Server Available
```

---

# Multi User Future Plan

Prepared for:

- User table
- Role based permissions
- Separate vector stores per user
- Separate document folders per user

Future data layout:

```
data/
  vector_store/{user_id}/
  documents/{user_id}/
```

---

# Security Model

| Feature            | Status      |
| ------------------ | ----------- |
| JWT authentication | Enabled     |
| Path validation    | Enforced    |
| Action validation  | Enforced    |
| Rate limiting      | Ready       |
| VPN first exposure | Recommended |

---

# Roadmap

## Phase 1

Refactor backend into modular architecture.

## Phase 2

Add file management endpoints.

## Phase 3

Add authentication layer.

## Phase 4

Add system automation.

## Phase 5

Enable remote VPN access.

## Phase 6

Add Wake on LAN integration.

## Phase 7

Add database for multi user.

---

# Long Term Vision

AI Server becomes:

- Personal knowledge engine
- Remote workstation assistant
- Project management AI
- Secure automation layer
- Fully private infrastructure

> Not a chatbot.  
> A personal AI system.
