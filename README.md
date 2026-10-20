# Astibosoft.Ai

Python RAG sidecar for the Astibosoft marketing chatbot (HardliqAi-style).

Owns **KnowledgeChunks** (+ `vector` extension) with its own migrate history (`AiSchemaVersions`). Does **not** migrate API tables (`Contacts`, `Admins`).

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/internal/ask` | `X-Internal-Key` when `RAG_INTERNAL_KEY` is set |
| `POST` | `/internal/embed` | same (202 + background reindex) |
| `GET` | `/health` | public |

Ask body: `{ "question": "..." }` → `{ "answer": "...", "sources": [...] }`  
(Compatible with Astibosoft.Api `IAiChatClient`.)

## Local

```bash
cd C:\Users\User\Astibosoft.Ai
copy Configuration\database.example.json Configuration\database.json
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

set RAG_INTERNAL_KEY=dev-internal-key
set GEMINI_API_KEY=your-gemini-key
set GEMINI_MODEL=gemini-3.1-flash-lite
uvicorn main:app --host 0.0.0.0 --port 8090
```

First start applies SQL migrations. Then embed knowledge:

```bash
curl -X POST http://localhost:8090/internal/embed -H "X-Internal-Key: dev-internal-key" -H "Content-Type: application/json" -d "{}"
```

Or set `AI_EMBED_ON_START=true`.

Knowledge files live in `knowledge/*.md` (`SourceKey` = file stem).

## VPS (with Astibosoft.Api deploy compose)

Ai is in `Astibosoft.Api/deploy/compose.vps.yaml`, published as **`127.0.0.1:8090`** (CLI only).

```bash
# from the VPS host
curl -s http://127.0.0.1:8090/health

curl -X POST http://127.0.0.1:8090/internal/embed \
  -H "X-Internal-Key: $AI_INTERNAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

API reaches Ai on the Docker network: `http://astibosoft-ai:8090` (no public internet exposure of Gemini).
