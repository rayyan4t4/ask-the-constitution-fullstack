"""RAG engine: ONNX MiniLM query encoder + FAISS retrieval + OpenRouter generation."""
import json
import os

import faiss
import numpy as np
import requests
from tokenizers import Tokenizer

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

_session = None
_tokenizer = None
_index = None
_chunks = None


def load():
    global _session, _tokenizer, _index, _chunks
    if _session is not None:
        return
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    _session = ort.InferenceSession(
        os.path.join(MODEL_DIR, "minilm.onnx"),
        sess_options=opts,
        providers=["CPUExecutionProvider"],
    )
    _tokenizer = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
    _tokenizer.enable_truncation(max_length=256)
    _tokenizer.enable_padding()
    _index = faiss.read_index(os.path.join(MODEL_DIR, "faiss.index"))
    _chunks = json.load(open(os.path.join(MODEL_DIR, "chunks.json")))
    assert _index.ntotal == len(_chunks), "index/chunk count mismatch"


def embed(texts):
    load()
    enc = _tokenizer.encode_batch(texts)
    ids = np.array([e.ids for e in enc], dtype=np.int64)
    mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
    types = np.zeros_like(ids)
    last_hidden = _session.run(None, {
        "input_ids": ids, "attention_mask": mask, "token_type_ids": types,
    })[0]
    mask_f = mask[:, :, None].astype(np.float32)
    summed = (last_hidden * mask_f).sum(axis=1)
    counts = mask_f.sum(axis=1).clip(min=1e-9)
    emb = summed / counts
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True).clip(min=1e-9)
    return emb.astype(np.float32)


def retrieve(question, k=5):
    load()
    q = embed([question])
    scores, idxs = _index.search(q, k)
    out = []
    for score, i in zip(scores[0], idxs[0]):
        c = _chunks[int(i)]
        out.append({
            "article": c["article"],
            "title": c["title"],
            "text": c["text"][:1200],
            "score": round(float(score), 4),
            "url": c["source"],
        })
    return out


SYSTEM = (
    "You answer questions about the Constitution of Pakistan using ONLY the excerpts provided. "
    "Cite the article number for every factual claim, e.g. (Article 19). "
    "If the excerpts do not contain the answer, say so plainly instead of guessing. "
    "Keep answers concise and in plain language."
)


def generate(question, sources):
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured on the server")
    context = "\n\n".join(
        f"[Article {s['article']}: {s['title']}]\n{s['text']}" for s in sources
    )
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.environ.get("LLM_MODEL", "poolside/laguna-s-2.1:free"),
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
