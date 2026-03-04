## Hybrid RAG inference flow (example)

Typical request to `/chat`:

```python
from backend.model.wrapper import handle_request

messages = [
    {"role": "system", "content": "You are a local assistant."},
    {"role": "user", "content": "Summarize the deployment notes from last week."},
]

response = handle_request(messages)
print(response)
```

Runtime workflow:

1. `wrapper.handle_request` logs incoming request context and routes the task.
2. `LocalRAG.search` checks **database chunks first** (`chunks.deleted = false`).
3. If DB misses, FAISS `.index` is searched and chunk ids are resolved against DB.
4. If DB rows are unavailable, `.docs` fallback metadata provides final context text.
5. Inference executes and writes structured logs to:
   - `backend/logs/app.log`
   - `backend/logs/inference.log`
   - `backend/logs/telemetry.log`
   - `backend/logs/rag.log`
   - `backend/logs/db.log`

Sample structured log line:

```json
{
  "timestamp": "2026-01-01T00:00:00.000000+00:00",
  "level": "INFO",
  "logger": "rag",
  "message": "rag_query",
  "event": "rag_query",
  "request_id": "2f9a8f67-0f8b-46d3-b31b-6ac6afc78f5a",
  "query": "deployment notes",
  "top_k": 4,
  "source": "index+database",
  "retrieved_ids": [41, 57, 62],
  "latency_seconds": 0.0084
}
```
