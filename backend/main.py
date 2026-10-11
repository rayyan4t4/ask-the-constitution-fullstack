"""Ask the Constitution — FastAPI backend."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Ask the Constitution API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.on_event("startup")
def startup():
    engine.load()


@app.get("/health")
def health():
    engine.load()
    return {"status": "ok", "chunks": len(engine._chunks)}


@app.post("/ask")
def ask(req: AskRequest):
    question = req.question.strip()
    try:
        sources = engine.retrieve(question, k=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"retrieval failed: {e}")
    if sources and sources[0]["score"] < 0.25:
        return {
            "answer": None,
            "sources": [],
            "message": "I couldn't find a relevant article for that question. Try asking about a specific right, institution, or procedure.",
        }
    try:
        answer = engine.generate(question, sources)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"generation failed: {e}")
    return {"answer": answer, "sources": sources, "message": None}
