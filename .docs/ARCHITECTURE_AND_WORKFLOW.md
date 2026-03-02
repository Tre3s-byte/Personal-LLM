# Personal-LLM: Technical Architecture and Execution Workflow

## 1. Scope and Intent

This document is a deep technical map of the current repository implementation. It is intended as a long-term memory artifact: if implementation details are forgotten, this paper should allow reconstruction of design intent, execution flow, and module responsibilities.

## 2. System Topology

The repository is structured as a multi-layer local AI platform:

- **Backend API layer (FastAPI)** for HTTP request handling.
- **Inference orchestration layer** for model routing, chunking strategies, and response synthesis.
- **Model layer** for lazy-loading llama.cpp models and caching loaded instances.
- **RAG layer** for document ingestion, embedding generation, and nearest-neighbor retrieval via FAISS.
- **Observability layer** with JSON logs and telemetry traces.
- **Metadata persistence layer** (SQLite/SQLAlchemy) for document and chunk records.
- **Frontend layer** (Vite + React starter) currently serving as a minimal UI scaffold.

## 3. Runtime Entry Points

### 3.1 Backend startup (`backend/app/main.py`)

Primary responsibilities:

1. Instantiate FastAPI app.
2. Install permissive CORS middleware.
3. Configure logging via `utils.logging.setup_logging()`.
4. Mount routers from `app.routes` and `api.routes`.
5. Initialize SQL schema with `Base.metadata.create_all(bind=engine)`.
6. Maintain an async RAG background ingestion path intended to load or build index artifacts.

### 3.2 Chat endpoint (`backend/api/routes.py`)

`POST /chat` pipeline:

1. Read and parse raw JSON body.
2. Validate `messages` schema (`[{role, content}, ...]`).
3. Route request using heuristic classifier (`services.router.route_request`).
4. If `requires_rag`, retrieve top chunks and inject a system context message.
5. Execute model inference through threadpool (`services.inference.run_routed_inference`).
6. Emit inference + telemetry logs.
7. Return normalized JSON response (`{"response": <text>}`).

## 4. Router and Strategy Selection

### 4.1 Router implementation (`backend/services/router.py`)

The router uses regex intent recognition and estimated token length to classify prompts into task families:

- code review / code heavy review
- grammar correction
- log review / log summary
- summarization
- recommendation
- generic short/long chat
- RAG query trigger

### 4.2 Strategy coupling

Router output includes:

- `target_model` (`small|medium|large`)
- `task_type`
- `chunk_strategy` (`None|chat|log|code`)
- `requires_rag` when applicable

The inference layer consumes this contract to choose either direct generation or two-stage chunk workflows.

## 5. Inference Pipeline

### 5.1 Core generation (`backend/services/inference.py`)

`_generate_with_model` behavior:

- validates model id against `MODEL_CONFIG`
- resolves model instance from `model.registry.get_model`
- normalizes history payload shape (`utils.normalization.normalize_history_for_model`)
- invokes llama.cpp chat completion
- normalizes usage accounting

### 5.2 Chunked strategies

- **Chat strategy**: trims message history to a safe context budget.
- **Log strategy**: chunk -> summarize each chunk -> merge summaries.
- **Code strategy**: chunk -> summarize blocks -> synthesize reasoning answer.

This architecture preserves answer quality for oversized payloads while maintaining context boundaries.

## 6. RAG Subsystem

### 6.1 Document ingestion (`backend/services/rag.py`)

`load_documents` recursively traverses configured paths, with guardrails:

- excluded directories (`config.EXCLUDED_DIRS`)
- hidden-file skip
- max file size filtering
- binary content skip (`\x00` detection)
- simple secret leakage regex filtering (`config.SECRET_PATTERNS`)
- PDF extraction via `PyPDF2` fallback path

### 6.2 Index lifecycle

`LocalRAG` owns:

- embedding service acquisition (`services.embeddings.get_embedding_service`)
- embedding normalization
- FAISS `IndexFlatL2` creation and query
- index persistence (`.index` + `.docs` plain text companion)

### 6.3 Retrieval flow

At query time:

1. embed query
2. normalize vector
3. FAISS nearest-neighbor search
4. map neighbor ids to original text chunks
5. return top-k chunk payloads for prompt injection

## 7. Model Management Layer

### 7.1 Loader (`backend/model/loader.py`)

Encapsulates llama.cpp object construction (`Llama`) with:

- configurable model path
- GPU layer offload count
- context length
- host thread count

### 7.2 Registry (`backend/model/registry.py`)

Provides lazy model initialization and process-local cache (`_model_cache`) to avoid repeated model reloads.

## 8. Token Budgeting and Chunking

### 8.1 `backend/services/chunker.py`

Implements lightweight heuristics:

- approximate token estimator (`len(text)>>2`)
- history trimming preserving system prompts
- log chunk segmentation by timestamp boundaries
- AST-aware and fallback chunking for source code text

These utilities support deterministic context management under constrained model windows.

## 9. Observability and Telemetry

### 9.1 Logging design (`backend/utils/logging.py`)

- JSON formatter with UTC timestamps.
- Rotating file handlers for:
  - app logs
  - inference logs
  - telemetry logs
- helper emitters for structured inference events.

Telemetry captures latency and token throughput (`tokens_per_second`) for downstream performance profiling.

## 10. Data and Persistence

### 10.1 SQLAlchemy models (`db/models.py`)

- `Document` table (`files`) tracks source-level metadata.
- `Chunk` table (`chunks`) represents embedded fragment records and lineage to source documents.

### 10.2 DB session (`db/session.py`)

Creates SQLite engine and declarative base used in startup table creation.

## 11. Frontend Status

`frontend/src/App.jsx` is currently the default Vite React counter demo. It is not yet wired to backend endpoints, and therefore should be treated as a placeholder shell rather than an integrated product interface.

## 12. Known Architectural Risks and Follow-up Targets

1. **Dual RAG initialization paths** exist (`app/main.py` and `api/routes.py`) and should be consolidated.
2. **Startup ingestion hook** should be explicitly attached to FastAPI lifecycle if background indexing is required at launch.
3. **Path defaults** in `config.py` include machine-specific locations and should be externalized.
4. **Session factory typo risk** in DB setup should be validated in runtime tests.
5. **RAG `.docs` serialization format** is line-based and may fragment multiline chunks; a structured format would improve fidelity.

## 13. Recommended Maintenance Protocol

When modifying the stack:

1. Update routing contract and inference consumers atomically.
2. Keep model config + registry expectations synchronized.
3. Preserve structured logging keys for dashboard compatibility.
4. Rebuild and smoke-test RAG retrieval whenever ingestion logic changes.
5. Maintain this document as the canonical architecture ledger.
