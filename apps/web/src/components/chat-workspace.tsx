"use client";

import { useState, useEffect } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { sendChatMessage, ChatResponse, getUniversities } from "@/lib/api";

interface ChatRequest {
  university: string;
  question: string;
}

function AnswerText({ text }: { text: string }) {
  const paragraphs = text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter((paragraph) => paragraph.length > 0);

  if (paragraphs.length === 0) {
    return <p className="answer-empty">The API returned an empty answer.</p>;
  }

  return (
    <div className="answer-text" data-testid="answer-text">
      {paragraphs.map((paragraph, index) => (
        <p key={index}>{paragraph}</p>
      ))}
    </div>
  );
}

export function ChatWorkspace() {
  const [universities, setUniversities] = useState<{ slug: string; name: string }[]>([]);
  const [university, setUniversity] = useState("demo");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [failedRequest, setFailedRequest] = useState<ChatRequest | null>(null);

  // Load universities on component mount
  useEffect(() => {
    async function loadUniversities() {
      try {
        const data = await getUniversities();
        setUniversities(data);
        // Set first university as default if available
        if (data.length > 0) {
          setUniversity(data[0].slug);
        }
      } catch (err) {
        console.error("Failed to load universities:", err);
        // Fallback to demo
        setUniversities([{ slug: "demo", name: "Demo University" }]);
      }
    }
    loadUniversities();
  }, []);

  const submitRequest = async (request: ChatRequest) => {
    setLoading(true);
    setError(null);
    setResponse(null);
    setFailedRequest(null);

    try {
      const data = await sendChatMessage(request.university, request.question);
      setResponse(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(message);
      setFailedRequest(request);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    void submitRequest({ university, question });
  };

  const handleRetry = () => {
    if (!failedRequest) return;
    void submitRequest(failedRequest);
  };

  return (
    <main id="main-content" className="container" tabIndex={-1}>
      <header className="header">
        <h1>OpenUni</h1>
        <p>Ask questions about any university and get cited answers.</p>
      </header>

      <form className="search-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <Label htmlFor="university">University</Label>
          <Select
            id="university"
            value={university}
            onChange={(e) => setUniversity(e.target.value)}
            disabled={loading}
          >
            {universities.map((uni) => (
              <option key={uni.slug} value={uni.slug}>
                {uni.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="form-group">
          <Label htmlFor="question">What do you want to know?</Label>
          <Input
            id="question"
            placeholder="e.g. What are the admission requirements for Computer Science?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            required
          />
        </div>

        <Button type="submit" block disabled={loading || !question.trim()}>
          {loading ? "Searching..." : "Ask Question"}
        </Button>

        {error && (
          <Alert className="mt-6">
            <p className="text-destructive-foreground">{error}</p>
            {failedRequest && (
              <Button type="button" block className="mt-3" onClick={handleRetry} disabled={loading}>
                Try again
              </Button>
            )}
          </Alert>
        )}
      </form>

      {loading && (
        <div className="loading-container" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Analyzing university documents...</p>
        </div>
      )}

      {response && !loading && (
        <section
          className="results-container"
          aria-labelledby="answer-heading"
          aria-live="polite"
        >
          <article className="answer-card">
            <div className="answer-header">
              <h2 id="answer-heading">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                Answer
              </h2>
              <span className="answer-source-count">
                {response.sources.length === 0
                  ? "No sources cited"
                  : `${response.sources.length} source${response.sources.length === 1 ? "" : "s"} cited`}
              </span>
            </div>
            <AnswerText text={response.answer} />
          </article>

          <section className="sources-section" aria-labelledby="sources-heading">
            <h3 id="sources-heading">
              Sources <span className="source-count">{response.sources.length}</span>
            </h3>
            {response.sources.length === 0 ? (
              <p className="sources-empty">
                No supporting sources were returned for this answer.
              </p>
            ) : (
              <ol className="sources-list">
                {response.sources.map((source, index) => (
                  <li className="source-card" key={`${source.source}-${index}`}>
                    <div className="source-meta">
                      <span className="source-index" aria-hidden="true">
                        {index + 1}
                      </span>
                      <span className="source-title">{source.source || "Unknown source"}</span>
                    </div>
                    <blockquote className="source-snippet">{source.text_snippet}</blockquote>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </section>
      )}
    </main>
  );
}
