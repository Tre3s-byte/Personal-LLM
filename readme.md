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

# Overview

**Personal self hosted AI infrastructure** designed to run locally, accessible remotely through a secure private network, and structured for future multi user expansion.

> This project is not a chatbot.  
> It is an AI operating layer for a personal workstation.

---

# Vision

AI Server provides:

- Local LLM inference
- Retrieval Augmented Generation over personal documents
- Secure file access
- Remote API access from phone
- Controlled system automation
- Wake on LAN integration
- Future multi user readiness

The goal is full ownership, privacy, and extensibility.

---

# Core Features

## 1. Local LLM Layer

- Fully offline capable
- GPU optional
- Interchangeable models
- Wrapped behind service interface abstraction

## 2. RAG Engine

- Local embeddings
- FAISS vector store
- Document ingestion pipeline
- Context injection before generation

## 3. File Access Layer

- Whitelisted directories only
- File listing
- File searching
- Document summarization
- Secure file download endpoint

## 4. System Automation Layer

- Controlled shutdown
- Restart
- Wake on LAN
- Predefined safe scripts only
- No arbitrary command execution

## 5. Secure API

- JWT authentication
- Role based structure ready
- Multi user compatible architecture

## 6. Remote Access

- Designed for VPN usage
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
Personal LLM/
│
├── backend/
│   ├── api/
│   ├── app/
│   ├── chats/
│   ├── logs/
│   ├── model/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── __pycache__/
│
├── frontend/
│   ├── node_modules/
│   └── ...
│
├── .venv/
├── .vscode/
├── .env
├── requirements.txt
├── setup.ps1
├── setup.sh
├── package.json
└── readme.md
```

Note: `node_modules` and `.venv` are development artifacts and should not be committed.

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

```
git clone <repo_url>
cd "Personal LLM"
```

## 2. Create Virtual Environment

Windows:

```
python -m venv .venv
.venv\Scripts\activate
```

Linux / Mac:

```
python -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```
pip install -r requirements.txt
```

## 4. Run Backend

```
uvicorn backend.app.main:app --reload
```

API documentation:

```
http://127.0.0.1:8000/docs
```

---

# LLM Configuration

The LLM layer is abstracted inside:

```
backend/services/
```

Supported backends may include:

- Ollama
- Local transformers
- llama.cpp

Models can be swapped without changing the API layer.

---

# RAG Workflow

1. Documents stored locally
2. Ingestion script generates embeddings
3. FAISS index stored locally
4. Query triggers similarity search
5. Context injected into prompt
6. LLM generates final answer

The RAG layer has no knowledge of HTTP or authentication.

---

# File System Security

Only whitelisted directories are accessible.

Example configuration:

```python
ALLOWED_PATHS = [
    "C:/Users/username/Documents",
    "C:/Users/username/Projects"
]
```

All file operations are validated against this list.

---

# System Automation Rules

Only predefined actions are executable.

Example:

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

Recommended: Tailscale VPN

Steps:

1. Install Tailscale on PC
2. Install Tailscale on phone
3. Connect both to same private network
4. Access API via Tailscale IP

No router port forwarding required.

---

# Wake on LAN Setup

Requirements:

- BIOS Wake on LAN enabled
- Network adapter configured
- Secondary device always online or router support

Optional flow:

```
Phone
  ↓
Small always on device
  ↓
Magic packet
  ↓
PC boots
  ↓
AI Server available
```

---

# Multi User Future Plan

Prepared architecture for:

- User table
- Role based permissions
- Separate vector stores per user
- Separate document folders per user

Future data layout:

```
data/
  ├── vector_store/{user_id}/
  └── documents/{user_id}/
```

---

# Security Model

- JWT authentication
- Path validation
- Action validation
- Rate limiting ready
- VPN first exposure strategy

---

# Roadmap

| Phase | Description                                |
| ----- | ------------------------------------------ |
| 1     | Refactor backend into modular architecture |
| 2     | Add file management endpoints              |
| 3     | Add authentication layer                   |
| 4     | Add system automation                      |
| 5     | Enable remote VPN access                   |
| 6     | Add Wake on LAN integration                |
| 7     | Add database for multi user support        |

---

# Long Term Vision

AI Server evolves into:

- Personal knowledge engine
- Remote workstation assistant
- Project management AI
- Secure automation layer
- Fully private infrastructure

Not a chatbot.  
A personal AI system.
