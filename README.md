# Ask the Constitution — full-stack edition

Production-style RAG over the Constitution of Pakistan: a FastAPI backend serving
retrieval + generation, and a React frontend.

- **Backend** (`backend/`): FastAPI. Query encoding with MiniLM-L6-v2 exported to ONNX
  (parity-verified: cosine 1.000 vs the torch model), FAISS retrieval over 768 chunks
  (323 articles + 5 schedules), answer generation via OpenRouter. Deployed on Render.
- **Frontend** (`frontend/`): Vite + React, hand-styled to match rayyankhan.online
  (Space Grotesk / Instrument Serif / JetBrains Mono, paper + ink + vivid orange).
  Deployed on Vercel.

## API

- `GET /health` → `{"status": "ok", "chunks": 768}`
- `POST /ask` `{"question": "..."}` → `{"answer": "...", "sources": [{article, title, text, score, url}]}`

Set `OPENROUTER_API_KEY` in the environment for answer generation.

## Evaluate

Retrieval quality measured on 30 hand-written questions with gold article labels
(see the original Streamlit project): hit-rate@1 0.867, hit-rate@3 0.933, hit-rate@5 1.000.
