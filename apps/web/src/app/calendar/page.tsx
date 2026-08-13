"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CalendarEntry,
  CalendarEntryType,
  getCalendar,
  getUniversities,
} from "@/lib/api";

const typeLabels: Record<CalendarEntryType, string> = {
  exam: "Exam",
  deadline: "Deadline",
  holiday: "Holiday",
  event: "Event",
};

function formatDate(date: string) {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(`${date}T00:00:00`));
}

function formatDateRange(entry: CalendarEntry) {
  if (!entry.end_date || entry.end_date === entry.date) {
    return formatDate(entry.date);
  }
  return `${formatDate(entry.date)} – ${formatDate(entry.end_date)}`;
}

export default function CalendarPage() {
  const [universities, setUniversities] = useState<{ slug: string; name: string }[]>([]);
  const [university, setUniversity] = useState("");
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadUniversities() {
      try {
        const data = await getUniversities();
        if (!active) return;
        setUniversities(data);
        setUniversity(data[0]?.slug ?? "");
      } catch (err) {
        console.error("Failed to load universities:", err);
        if (!active) return;
        setUniversities([{ slug: "demo", name: "Demo University" }]);
        setUniversity("demo");
      }
    }

    loadUniversities();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!university) return;

    let active = true;

    async function loadCalendar() {
      await Promise.resolve();
      if (!active) return;
      setLoading(true);
      setError(null);
      setEntries([]);

      try {
        const data = await getCalendar(university);
        if (active) setEntries(data);
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "An unexpected error occurred.";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadCalendar();
    return () => {
      active = false;
    };
  }, [university]);

  const sortedEntries = useMemo(
    () => [...entries].sort((a, b) => a.date.localeCompare(b.date)),
    [entries]
  );

  return (
    <main className="container">
      <header className="header calendar-header">
        <h1>Academic Calendar</h1>
        <p>Keep track of upcoming exams, deadlines, holidays, and university events.</p>
      </header>

      <section className="calendar-controls" aria-label="Calendar settings">
        <div className="form-group calendar-university-field">
          <label htmlFor="university">University</label>
          <select
            id="university"
            value={university}
            onChange={(event) => setUniversity(event.target.value)}
            disabled={loading || universities.length === 0}
          >
            {universities.map((uni) => (
              <option key={uni.slug} value={uni.slug}>
                {uni.name}
              </option>
            ))}
          </select>
        </div>
      </section>

      {loading && (
        <div className="loading-container" role="status">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading calendar entries...</p>
        </div>
      )}

      {error && !loading && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && university && sortedEntries.length === 0 && (
        <div className="empty-state">
          <h2>No calendar entries</h2>
          <p>This university has not published any calendar dates yet.</p>
        </div>
      )}

      {!loading && !error && sortedEntries.length > 0 && (
        <section className="calendar-list" aria-label="Calendar entries">
          {sortedEntries.map((entry, index) => (
            <article className="calendar-card" key={`${entry.date}-${entry.title}-${index}`}>
              <div className="calendar-card-meta">
                <span className={`calendar-type calendar-type-${entry.type}`}>
                  {typeLabels[entry.type]}
                </span>
                <time dateTime={entry.date}>{formatDateRange(entry)}</time>
              </div>
              <h2>{entry.title}</h2>
              {entry.description && <p>{entry.description}</p>}
              {entry.source_url && (
                <a href={entry.source_url} target="_blank" rel="noreferrer">
                  View official source <span aria-hidden="true">↗</span>
                </a>
              )}
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
