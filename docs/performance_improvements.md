# Tarot Reading Engine Performance Improvements

## Snapshot — 2025-11-01

### 1. Remove Artificial `asyncio.sleep` Delays
- File: `backend/src/api/routes/readings_stream.py:184`, `:226`, `:272`, `:449`, `:458`, `:466`, `:474`
- Issue: Fixed `await asyncio.sleep(...)` calls inject ~0.8–1.0 s of intentional delay during SSE streaming.
- Recommendation: Skip these sleeps (or gate behind `settings.DEBUG`) so production responses flush immediately.

### 2. Decouple Firestore Persistence From SSE Response
- [2025-11-01] Firestore writes are now queued via background tasks, and Firestore provider uses a single batch commit with caller-provided IDs.
- Files: `backend/src/api/routes/readings_stream.py:532`, `backend/src/database/firestore_provider.py:336`, `:356`
- Issue: Reading completion waits on Firestore writes (document + subcollection), delaying the `complete` event.
- Recommendation: Persist via FastAPI `BackgroundTasks` or a queue. For synchronous fallback, batch card inserts with a Firestore `write_batch` to minimize round-trips.

### 3. Cache Knowledge Base JSON Loads
- File: `backend/src/ai/rag/knowledge_base.py:49`, `:124`, `:161`
- Issue: Every RAG request re-opens JSON files, adding repetitive disk I/O.
- Recommendation: Memoize card/spread/category loads using `functools.lru_cache` or a module-level cache warmed on startup.

### 4. Reuse SentenceTransformer Encodings
- Files: `backend/src/ai/rag/retriever.py:118`, `:137`, `backend/src/ai/rag/vector_store.py:73`, `:114`
- Issue: Each retrieval spins up `run_in_executor` jobs that recompute embeddings, competing for CPU.
- Recommendation: Introduce an embedding cache per (query, k) or pre-encode frequent prompts; reuse within a single reading request to cut executor overhead.

### 5. Stream LLM Output or Refine Retry Strategy
- Files: `backend/src/api/routes/readings_stream.py:346`, `:365`, `backend/src/ai/orchestrator.py:228`, `backend/src/ai/providers/claude_provider.py:96`
- Issue: Parse failures trigger full generations with 90 s timeouts, inflating tail latency.
- Recommendation: Explore Anthropic streaming to emit tokens progressively, or add lightweight repair passes that avoid full re-generation when parsing errors occur.
