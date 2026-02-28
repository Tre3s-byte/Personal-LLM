<p align="center"> 
    <h1 align="center">Personal AI Server</h1> 
    <p align="center"> Self Hosted · Local LLM · RAG Engine · Remote Access Ready </p> 
</p> 
<p align="center"> 
    <img src="https://img.shields.io/badge/LLM-Local-blue" /> 
    <img src="https://img.shields.io/badge/RAG-FAISS-green" /> 
    <img src="https://img.shields.io/badge/API-FastAPI-purple" /> 
    <img src="https://img.shields.io/badge/Access-VPN-orange" /> 
    <img src="https://img.shields.io/badge/License-MIT-lightgrey" /> 
</p>

---

**Personal self hosted AI** infrastructure designed to run locally, accessible remotely through a secure private network, and structured for future multi user expansion.

**This project is not a chatbot.**
It is an AI operating layer for a personal workstation.

---

##Vision

**AI Server provides:**

• Local LLM inference

• Retrieval Augmented Generation over personal documents

• Secure file access

• Remote API access from phone

• Controlled system automation

• Wake on LAN integration

• Future multi user readiness

The goal is full ownership, privacy, and extensibility.

---

##Core Features

1. Local LLM Layer

Runs fully offline

GPU optional

Model interchangeable

Wrapped behind a service interface

2. RAG Engine

Local embeddings

FAISS vector store

Document ingestion pipeline

Context injection before generation

3. File Access Layer

Whitelisted directories only

List files

Search files

Read and summarize documents

Secure file download endpoint

4. System Automation Layer

Controlled shutdown

Restart

Wake on LAN

Predefined safe scripts only

No arbitrary command execution

5. Secure API

JWT authentication

Role based structure ready

Multi user compatible architecture

6. Remote Access

Designed for VPN usage (Tailscale recommended)

No public port exposure required

High Level Architecture

Phone
↓
VPN (Tailscale)
↓
FastAPI Backend
↓
Service Layer
↓
LLM + Vector Store + Filesystem

Each layer is isolated and replaceable.

Project Structure
ai-server/
│
├── app/
│ ├── main.py
│ ├── config.py
│
│ ├── api/
│ │ ├── chat.py
│ │ ├── files.py
│ │ ├── system.py
│ │ ├── auth.py
│
│ ├── services/
│ │ ├── llm_service.py
│ │ ├── rag_service.py
│ │ ├── embedding_service.py
│ │ ├── file_service.py
│ │ ├── system_service.py
│
│ ├── core/
│ │ ├── security.py
│ │ ├── dependencies.py
│
│ ├── models/
│ │ ├── schemas.py
│
├── data/
│ ├── vector_store/
│ ├── documents/
│
├── scripts/
│ ├── ingest.py
│ ├── wake_pc.py
│
├── requirements.txt
├── README.md
Design Principles

Separation of concerns

Service oriented architecture

No direct filesystem exposure

Authentication required for every endpoint

All system actions validated and restricted

Multi user ready from day one

Installation

1. Clone repository
   git clone <repo_url>
   cd ai-server
2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate
3. Install dependencies
   pip install -r requirements.txt
4. Run server
   uvicorn app.main:app --reload

API documentation available at:

http://127.0.0.1:8000/docs

LLM Configuration

The LLM layer is abstracted inside:

app/services/llm_service.py

Supported backends:

Ollama

Local transformers

llama.cpp

Model can be swapped without changing API layer.

RAG Workflow

Documents placed in data/documents

Ingestion script generates embeddings

FAISS index stored in data/vector_store

Query triggers similarity search

Context injected into prompt

LLM generates answer

The RAG layer has no knowledge of HTTP or authentication.

File System Security

Only whitelisted directories are accessible.

Configured in config.py:

ALLOWED_PATHS = [
"C:/Users/username/Documents",
"C:/Users/username/Projects"
]

All file operations are validated against this list.

System Automation Rules

Only predefined actions are executable.

Example:

ALLOWED_ACTIONS = {
"shutdown": shutdown_pc,
"restart": restart_pc,
"backup": run_backup
}

No arbitrary shell execution allowed.

Remote Access Setup

Recommended: Tailscale VPN

Steps:

Install Tailscale on PC

Install Tailscale on phone

Connect both to same network

Access API via Tailscale IP

No router port forwarding required.

Wake on LAN Setup

Requirements:

BIOS Wake on LAN enabled

Network adapter configured

Secondary device always online or router support

Optional architecture:
Phone → small always on device → magic packet → PC boots → AI server available

Multi User Future Plan

Prepared for:

User table

Role based permissions

Separate vector stores per user

Separate document folders per user

Data layout future ready:

data/
vector_store/{user_id}/
documents/{user_id}/
Security Model

JWT authentication

Path validation

Action validation

Rate limiting ready

VPN first exposure strategy

Roadmap

Phase 1:
Refactor backend into modular architecture

Phase 2:
Add file management endpoints

Phase 3:
Add authentication layer

Phase 4:
Add system automation

Phase 5:
Enable remote VPN access

Phase 6:
Add Wake on LAN integration

Phase 7:
Add database for multi user

Long Term Vision

AI Server becomes:

Personal knowledge engine

Remote workstation assistant

Project management AI

Secure automation layer

Fully private infrastructure

Not a chatbot.
A personal AI system.
