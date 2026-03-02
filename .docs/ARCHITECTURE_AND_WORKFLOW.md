# Personal-LLM: Technical Architecture and Execution Workflow

## 1. Scope and Intent

This document defines the complete architectural blueprint of the Personal-LLM system. It serves as a reconstruction reference for system behavior, module boundaries, execution flow, and persistence strategy.

The platform is a local-first AI orchestration stack composed of:

- FastAPI backend
- Llama.cpp model runtime
- Router-driven inference strategies
- SQLite-backed RAG storage
- YouTube backup ingestion tool
- Structured logging and telemetry

---

## 2. System Topology

The repository is organized into layered responsibilities:

### 2.1 API Layer

FastAPI application responsible for:

- Request validation
- Routing
- Lifecycle hooks
- Dependency injection

### 2.2 Inference Orchestration Layer

Handles:

- Intent classification
- Model selection
- Chunk strategies
- RAG injection
- Response synthesis

### 2.3 Model Runtime Layer

- Lazy llama.cpp model loading
- Model instance caching
- Context window management

### 2.4 RAG Layer (SQLite-backed)

Responsible for:

- Document ingestion
- Chunk creation
- Embedding generation
- Vector persistence inside SQLite
- Nearest neighbor retrieval

### 2.5 Tools Layer

Contains system tools such as:

- YouTube backup downloader
- External ingestion utilities

### 2.6 Observability Layer

- JSON structured logs
- Rotating log files
- Telemetry metrics

---

## 3. Runtime Entry Points

### 3.1 Backend Startup

File: backend/app/main.py

Responsibilities:

1. Create FastAPI instance
2. Configure CORS
3. Initialize structured logging
4. Mount API routers
5. Initialize SQLite schema
6. Initialize RAG service
7. Optionally trigger background indexing

---

## 4. Chat Execution Flow

### Endpoint

POST /chat

Execution pipeline:

1. Parse JSON payload
2. Validate message schema
3. Route request via heuristic classifier
4. If `requires_rag = True`
   - Query SQLite vector store
   - Inject top-k chunks into system context
5. Execute inference in threadpool
6. Emit telemetry
7. Return normalized response

---

## 5. Router and Strategy Selection

File: backend/services/router.py

The router performs lightweight intent recognition using:

- Regex classification
- Token length estimation
- Keyword detection

It outputs a routing contract:

```python
{
    "target_model": "small|medium|large",
    "task_type": "...",
    "chunk_strategy": "chat|log|code|None",
    "requires_rag": bool
}
```

This contract drives inference behavior.

```
class Chunk(Base):
**tablename** = "chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text)
    embedding = Column(LargeBinary)
    created_at = Column(DateTime)
```

Embeddings are stored as serialized float arrays in binary format.

## 7.2 Ingestion Pipeline

**File:**  
backend/services/rag.py

### Document Ingestion Flow

1. Traverse configured directories
2. Skip
   - Hidden files
   - Excluded directories
   - Large files
   - Binary files
3. Extract content
4. Chunk text
5. Generate embeddings
6. Persist
   - Document metadata
   - Chunk content
   - Serialized embedding vectors

Embeddings are normalized before storage.

---

## 7.3 Retrieval Flow

At query time:

1. Embed query text
2. Normalize query vector
3. Fetch candidate embeddings from SQLite
4. Compute cosine similarity in memory
5. Return top-k chunk texts

This replaces FAISS with database backed vector persistence.

---

## 8. YouTube Backup Tool

**File:**  
backend/tools/youtube_backup_downloader.py

### Purpose

Provides offline ingestion of YouTube and YouTube Music URLs for archival and RAG indexing.

### Responsibilities

- Accept YouTube or YouTube Music URL
- Extract
  - Title
  - Author
  - Description
  - Metadata
- Download audio or metadata
- Store transcript or metadata into the RAG ingestion pipeline

### Integration Flow

1. Tool invoked via router intent
2. Downloader fetches metadata
3. Transcript or description is chunked
4. Content is stored as Document and Chunks in SQLite
5. Embeddings are generated and persisted

This makes YouTube content searchable through RAG queries.

---

## 9. Model Management

### Loader

**File:**  
backend/model/loader.py

Wraps llama.cpp initialization:

- Model path
- GPU layer count
- Context size
- Thread configuration

### Registry

**File:**  
backend/model/registry.py

Provides:

- Lazy loading
- In process caching
- Singleton access pattern

Prevents repeated model reload overhead.

---

## 10. Chunking and Token Budgeting

**File:**  
backend/services/chunker.py

Provides:

- Approximate token estimation
- Context trimming
- Log segmentation
- Code aware chunking

Ensures inference remains within context window constraints.

---

## 11. Observability

**File:**  
backend/utils/logging.py

Features:

- JSON structured logs
- Rotating file handlers
- UTC timestamps

Inference metrics include:

- Latency
- Token throughput
- Model id
- Task type

---

## 12. Persistence Layer

**File:**  
backend/db/session.py

Creates:

```python
engine = create_engine("sqlite:///personal_llm.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

Tables are created at startup via:

```
Base.metadata.create_all(bind=engine)
```

## 13. Updated Architectural Guarantees

- No JSON based RAG storage remains

- All embeddings are persisted in SQLite

- YouTube content becomes first class searchable documents

- Model loading is lazy and cached

- Router contract is stable across inference consumers

## 14. Maintenance Protocol

1. When modifying the system:

2. pdate router and inference contracts together

3. Keep model config aligned with registry behavior

4. Maintain logging schema compatibility

5. Re index RAG when ingestion logic changes

6. Keep this document synchronized with structural changes

## 15. Long Term Design Direction

- Future improvements may include:

- SQLite vector indexing via extension

- Async ingestion workers

- Frontend integration

- Incremental embedding updates

- Background re index scheduler
