import { useState, useRef, useEffect } from "react";
import "./index.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const EXAMPLES = [
  "What does the constitution say about freedom of speech?",
  "Is there a right to a fair trial?",
  "How can the constitution be amended?",
  "When can emergency be proclaimed?",
];

function renderAnswer(text) {
  const parts = text.split(/(\(Article [\dA-Z]+\))/g);
  return parts.map((p, i) =>
    /^\(Article [\dA-Z]+\)$/.test(p)
      ? <span key={i} className="cite">{p}</span>
      : <span key={i}>{p}</span>
  );
}

export default function App() {
  const [q, setQ] = useState("");
  const [state, setState] = useState("idle");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [notice, setNotice] = useState(null);
  const [openSrc, setOpenSrc] = useState(null);
  const abortRef = useRef(null);

  async function ask(question) {
    const query = (question ?? q).trim();
    if (query.length < 3 || state === "searching" || state === "answering") return;
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    setQ(query);
    setState("searching");
    setAnswer(null); setSources([]); setNotice(null); setOpenSrc(null);
    try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query }),
        signal: ctl.signal,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      if (data.message && !data.answer) {
        setNotice(data.message);
        setState("idle");
        return;
      }
      setState("answering");
      setSources(data.sources || []);
      const full = data.answer || "";
      setAnswer("");
      setState("done");
      let i = 0;
      const tick = () => {
        i += 3;
        setAnswer(full.slice(0, i));
        if (i < full.length) setTimeout(tick, 12);
      };
      tick();
    } catch (e) {
      if (e.name === "AbortError") return;
      setNotice("Something went wrong reaching the server. Please try again.");
      setState("error");
    }
  }

  useEffect(() => () => abortRef.current?.abort(), []);
  const busy = state === "searching" || state === "answering";

  return (
    <div className="page">
      <header className="topbar">
        <div className="wrap topbar-in">
          <span className="brand"><span className="brand-mark">§</span> Ask the Constitution</span>
          <span className="top-meta">Pakistan · Constitution 1973 <a href="https://github.com/rayyan4t4/ask-the-constitution-pakistan" target="_blank" rel="noreferrer">GitHub ↗</a></span>
        </div>
      </header>

      <main className="wrap">
        <section className="hero">
          <p className="kicker">Retrieval-augmented Q&amp;A · 323 articles + 5 schedules</p>
          <h1>Ask the Constitution<span className="accent-dot">.</span><br /><em>Answered with citations.</em></h1>
          <p className="lede">Ask in plain language. Every answer is grounded in the actual articles — cited, sourced, and linked to the full text.</p>
        </section>

        <section className="panel">
          <div className="askrow">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask()}
              placeholder="e.g. What are the qualifications to become a member of parliament?"
              aria-label="Your question"
            />
            <button onClick={() => ask()} disabled={busy || q.trim().length < 3}>
              {busy ? "Working…" : "Ask"}
            </button>
          </div>
          <div className="chips">
            {EXAMPLES.map((ex) => (
              <button key={ex} className="chip" onClick={() => ask(ex)} disabled={busy}>{ex}</button>
            ))}
          </div>

          {state === "searching" && <p className="status"><span className="pulse" />Searching 323 articles…</p>}
          {state === "answering" && <p className="status"><span className="pulse" />Drafting answer from the articles…</p>}
          {notice && <p className="notice">{notice}</p>}

          {answer !== null && (
            <div className="result">
              <h2>Answer</h2>
              <p className="answer">{renderAnswer(answer)}</p>
            </div>
          )}

          {sources.length > 0 && (
            <div className="result">
              <h2>Sources</h2>
              <ol className="sources">
                {sources.map((s, i) => (
                  <li key={s.article + i} className={openSrc === i ? "open" : ""}>
                    <button className="src-head" onClick={() => setOpenSrc(openSrc === i ? null : i)}>
                      <span className="src-num">{String(i + 1).padStart(2, "0")}</span>
                      <span className="src-title">Article {s.article}: {s.title}</span>
                      <span className="src-arrow">{openSrc === i ? "−" : "+"}</span>
                    </button>
                    {openSrc === i && (
                      <div className="src-body">
                        <p>{s.text}</p>
                        <a href={s.url} target="_blank" rel="noreferrer">Read full article ↗</a>
                      </div>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>

        <footer className="foot">
          <p>Informational only — not legal advice. Text: Constitution of Pakistan (1973, as amended), via pakistani.org.</p>
          <p>Built by <a href="https://rayyankhan.online" target="_blank" rel="noreferrer">Rayyan Khan</a> · MiniLM + FAISS retrieval, cited generation</p>
        </footer>
      </main>
    </div>
  );
}
