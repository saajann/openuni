"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  getUniversities,
  sendChatMessage,
  type ChatResponse,
  type University,
} from "@/lib/api";

const DEFAULT_UNIVERSITY_SLUG = "demo";

export default function Home() {
  const [universities, setUniversities] = useState<University[]>([]);
  const [universitySlug, setUniversitySlug] = useState(DEFAULT_UNIVERSITY_SLUG);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Best-effort: if this fails (API down, CORS, etc.) we silently keep
    // the "demo" fallback so the page is still usable for asking questions.
    getUniversities()
      .then((list) => {
        if (list.length > 0) {
          setUniversities(list);
          setUniversitySlug(list[0].slug);
        }
      })
      .catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await sendChatMessage(universitySlug, question);
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>OpenUni</h1>
      <p>Ask a question about your university and get a cited answer.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <label htmlFor="university-select">University</label>
        {universities.length > 0 ? (
          <select
            id="university-select"
            value={universitySlug}
            onChange={(e) => setUniversitySlug(e.target.value)}
          >
            {universities.map((u) => (
              <option key={u.slug} value={u.slug}>
                {u.name}
              </option>
            ))}
          </select>
        ) : (
          <select id="university-select" value={universitySlug} disabled>
            <option value={DEFAULT_UNIVERSITY_SLUG}>demo</option>
          </select>
        )}

        <label htmlFor="question-input">Question</label>
        <textarea
          id="question-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          placeholder="e.g. When is the deadline to apply for the fall semester?"
        />

        <button type="submit" disabled={isLoading || !question.trim()}>
          {isLoading ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && (
        <div role="alert" style={{ marginTop: "1.5rem", color: "#b00020" }}>
          {error}
        </div>
      )}

      {result && (
        <section style={{ marginTop: "1.5rem" }}>
          <h2>Answer</h2>
          <p>{result.answer}</p>

          {result.sources.length > 0 && (
            <>
              <h3>Sources</h3>
              <ul>
                {result.sources.map((source, i) => (
                  <li key={i}>
                    <em>&ldquo;{source.text_snippet}&rdquo;</em> — {source.source}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </main>
  );
}
