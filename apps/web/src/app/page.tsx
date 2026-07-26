"use client";

import { useState } from "react";
import { sendChatMessage, ChatResponse } from "@/lib/api";

export default function Home() {
  const [university, setUniversity] = useState("demo");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await sendChatMessage(university, question);
      setResponse(data);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <header className="header">
        <h1>OpenUni</h1>
        <p>Ask questions about any university and get cited answers.</p>
      </header>

      <form className="search-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="university">University</label>
          <select
            id="university"
            value={university}
            onChange={(e) => setUniversity(e.target.value)}
            disabled={loading}
          >
            <option value="demo">Demo University</option>
            {/* Additional universities can be loaded here in the future */}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="question">What do you want to know?</label>
          <input
            type="text"
            id="question"
            placeholder="e.g. What are the admission requirements for Computer Science?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            required
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading || !question.trim()}>
          {loading ? "Searching..." : "Ask Question"}
        </button>

        {error && <div className="error-message">{error}</div>}
      </form>

      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Analyzing university documents...</p>
        </div>
      )}

      {response && !loading && (
        <div className="results-container">
          <div className="answer-card">
            <h2>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              Answer
            </h2>
            <div dangerouslySetInnerHTML={{ __html: response.answer.replace(/\n/g, '<br/>') }} />
          </div>

          {response.sources.length > 0 && (
            <div className="sources-section">
              <h3>Sources ({response.sources.length})</h3>
              <div className="sources-grid">
                {response.sources.map((source, index) => (
                  <div key={index} className="source-card">
                    <div className="source-title">{source.source}</div>
                    <div className="source-snippet">"{source.text_snippet}"</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
