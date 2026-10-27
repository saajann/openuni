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
    month: "short",
    year: "numeric",
  }).format(new Date(`${date}T00:00:00`));
}

function formatDateRange(entry: CalendarEntry) {
  if (!entry.end_date || entry.end_date === entry.date) {
    return formatDate(entry.date);
  }

  return `${formatDate(entry.date)} – ${formatDate(entry.end_date)}`;
}

function formatDay(date: string) {
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
  }).format(new Date(`${date}T00:00:00`));
}

function formatMonth(date: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
  }).format(new Date(`${date}T00:00:00`));
}

export default function CalendarPage() {
  const [universities, setUniversities] = useState<
    { slug: string; name: string }[]
  >([]);
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
      setLoading(true);
      setError(null);
      setEntries([]);

      try {
        const data = await getCalendar(university);

        if (active) {
          setEntries(data);
        }
      } catch (err) {
        if (!active) return;

        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred."
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadCalendar();

    return () => {
      active = false;
    };
  }, [university]);

  const sortedEntries = useMemo(
    () =>
      [...entries].sort((a, b) => {
        const dateComparison = a.date.localeCompare(b.date);

        if (dateComparison !== 0) return dateComparison;

        return a.title.localeCompare(b.title);
      }),
    [entries]
  );

  return (
    <main className="container calendar-page">
      <header className="header calendar-header">
        <p className="calendar-eyebrow">YOUR ACADEMIC YEAR</p>
        <h1>Academic Calendar</h1>
        <p>
          Keep track of upcoming exams, deadlines, holidays, and university
          events in one place.
        </p>
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

        <p className="calendar-controls-hint">
          Select a university to view its published academic dates.
        </p>
      </section>

      {loading && (
        <div className="calendar-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Loading academic events...</p>
        </div>
      )}

      {error && !loading && (
        <div className="error-message" role="alert">
          <h2>Unable to load the calendar</h2>
          <p>{error}</p>
          <p>Please try again later.</p>
        </div>
      )}

      {!loading && !error && university && sortedEntries.length === 0 && (
        <div className="empty-state" role="status">
          <span className="calendar-empty-icon" aria-hidden="true">
            ◷
          </span>
          <h2>No calendar entries yet</h2>
          <p>
            This university has not published any calendar dates yet. Check
            again later for updates.
          </p>
        </div>
      )}

      {!loading && !error && sortedEntries.length > 0 && (
        <section className="calendar-agenda" aria-label="Academic agenda">
          <div className="calendar-agenda-heading">
            <div>
              <p className="calendar-eyebrow">STAY ORGANIZED</p>
              <h2>Academic agenda</h2>
            </div>

            <span className="calendar-event-count">
              {sortedEntries.length}{" "}
              {sortedEntries.length === 1 ? "event" : "events"}
            </span>
          </div>

          <ol className="calendar-list">
            {sortedEntries.map((entry, index) => (
              <li
                className="calendar-timeline-item"
                key={`${entry.date}-${entry.title}-${index}`}
              >
                <div className="calendar-date-marker" aria-hidden="true">
                  <span>{formatDay(entry.date)}</span>
                  <span>{formatMonth(entry.date)}</span>
                </div>

                <article
                  className={`calendar-card calendar-card-${entry.type}`}
                >
                  <div className="calendar-card-meta">
                    <span
                      className={`calendar-type calendar-type-${entry.type}`}
                    >
                      {typeLabels[entry.type]}
                    </span>

                    <time dateTime={entry.date}>
                      {formatDateRange(entry)}
                    </time>
                  </div>

                  <h3>{entry.title}</h3>

                  {entry.description && <p>{entry.description}</p>}

                  {entry.source_url && (
                    <a
                      href={entry.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View official source{" "}
                      <span aria-hidden="true">↗</span>
                      <span className="sr-only">
                        {" "}
                        (opens in a new tab)
                      </span>
                    </a>
                  )}
                </article>
              </li>
            ))}
          </ol>
        </section>
      )}
    </main>
  );
}
