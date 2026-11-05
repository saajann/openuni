"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
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

const calendarTypes = Object.keys(typeLabels) as CalendarEntryType[];

interface CalendarFilterState {
  type: CalendarEntryType | "";
  from: string;
  to: string;
}

function isCalendarType(value: string | null): value is CalendarEntryType {
  return value !== null && calendarTypes.includes(value as CalendarEntryType);
}

function isIsoDate(value: string | null): value is string {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;

  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function readFilters(params: { get: (name: string) => string | null }): CalendarFilterState {
  const type = params.get("type");
  const from = params.get("from");
  const to = params.get("to");

  return {
    type: isCalendarType(type) ? type : "",
    from: isIsoDate(from) ? from : "",
    to: isIsoDate(to) ? to : "",
  };
}

function validateFilters(filters: CalendarFilterState): string | null {
  if (filters.from && filters.to && filters.from > filters.to) {
    return "The start date must be on or before the end date.";
  }

  return null;
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(`${date}T00:00:00`));
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

export function CalendarView() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlKey = searchParams.toString();
  const initialFilters = readFilters(searchParams);
  const [lastUrlKey, setLastUrlKey] = useState(urlKey);
  const [universities, setUniversities] = useState<{ slug: string; name: string }[]>([]);
  const [university, setUniversity] = useState("");
  const [typeFilter, setTypeFilter] = useState<CalendarEntryType | "">(initialFilters.type);
  const [fromFilter, setFromFilter] = useState(initialFilters.from);
  const [toFilter, setToFilter] = useState(initialFilters.to);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (urlKey !== lastUrlKey) {
    const nextFilters = readFilters(searchParams);
    setLastUrlKey(urlKey);
    setTypeFilter(nextFilters.type);
    setFromFilter(nextFilters.from);
    setToFilter(nextFilters.to);
  }

  const validationError = validateFilters({
    type: typeFilter,
    from: fromFilter,
    to: toFilter,
  });
  const hasActiveFilters = Boolean(typeFilter || fromFilter || toFilter);
  const isLoading = loading && !validationError;

  useEffect(() => {
    let active = true;

    async function loadUniversities() {
      try {
        const data = await getUniversities();
        if (!active) return;
        setUniversities(data);
        setUniversity((current) => current || data[0]?.slug || "");
      } catch (err) {
        console.error("Failed to load universities:", err);
        if (!active) return;
        setUniversities([{ slug: "demo", name: "Demo University" }]);
        setUniversity((current) => current || "demo");
      }
    }

    loadUniversities();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!university || validationError) return;

    let active = true;

    async function loadCalendar() {
      setLoading(true);
      setError(null);
      setEntries([]);

      try {
        const filters: { type?: CalendarEntryType; from?: string; to?: string } = {};
        if (typeFilter) filters.type = typeFilter;
        if (fromFilter) filters.from = fromFilter;
        if (toFilter) filters.to = toFilter;

        const data = await getCalendar(university, filters);
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
  }, [university, typeFilter, fromFilter, toFilter, validationError]);

  function updateFilters(patch: Partial<CalendarFilterState>) {
    const next: CalendarFilterState = {
      type: typeFilter,
      from: fromFilter,
      to: toFilter,
      ...patch,
    };
    const params = new URLSearchParams(searchParams.toString());

    if (next.type) params.set("type", next.type);
    else params.delete("type");
    if (next.from) params.set("from", next.from);
    else params.delete("from");
    if (next.to) params.set("to", next.to);
    else params.delete("to");

    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });

    setTypeFilter(next.type);
    setFromFilter(next.from);
    setToFilter(next.to);
  }

  function clearFilters() {
    updateFilters({ type: "", from: "", to: "" });
  }

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
    <main id="main-content" className="container" tabIndex={-1}>
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
            disabled={isLoading || universities.length === 0}
          >
            {universities.map((uni) => (
              <option key={uni.slug} value={uni.slug}>
                {uni.name}
              </option>
            ))}
          </select>
        </div>

        <div className="calendar-filters" role="group" aria-labelledby="calendar-filters-heading">
          <div className="calendar-filters-heading">
            <h2 id="calendar-filters-heading">Filter calendar</h2>
            {hasActiveFilters && (
              <button type="button" className="btn-secondary" onClick={clearFilters}>
                Clear filters
              </button>
            )}
          </div>

          <div className="calendar-filter-grid">
            <div className="form-group">
              <label htmlFor="calendar-type">Entry type</label>
              <select
                id="calendar-type"
                value={typeFilter}
                onChange={(event) =>
                  updateFilters({
                    type: event.target.value as CalendarEntryType | "",
                  })
                }
              >
                <option value="">All types</option>
                {calendarTypes.map((type) => (
                  <option key={type} value={type}>
                    {typeLabels[type]}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="calendar-from">From</label>
              <input
                id="calendar-from"
                type="date"
                value={fromFilter}
                onChange={(event) => updateFilters({ from: event.target.value })}
                aria-invalid={validationError ? true : undefined}
                aria-describedby={validationError ? "calendar-date-error" : undefined}
              />
            </div>

            <div className="form-group">
              <label htmlFor="calendar-to">To</label>
              <input
                id="calendar-to"
                type="date"
                value={toFilter}
                onChange={(event) => updateFilters({ to: event.target.value })}
                aria-invalid={validationError ? true : undefined}
                aria-describedby={validationError ? "calendar-date-error" : undefined}
              />
            </div>
          </div>

          {validationError && (
            <p className="field-error" id="calendar-date-error" role="alert">
              {validationError}
            </p>
          )}
        </div>
      </section>

      {isLoading && (
        <div className="loading-container" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading calendar entries...</p>
        </div>
      )}

      {error && !isLoading && !validationError && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {!isLoading &&
        !error &&
        !validationError &&
        university &&
        sortedEntries.length === 0 && (
          <div className="empty-state">
            <h2>No calendar entries</h2>
            <p>
              This university has not published any calendar dates yet
              {hasActiveFilters ? " matching these filters" : ""}.
            </p>
          </div>
        )}

      {!isLoading && !error && !validationError && sortedEntries.length > 0 && (
        <section className="calendar-agenda" aria-labelledby="calendar-agenda-heading">
          <div className="calendar-agenda-heading">
            <div>
              <p className="calendar-eyebrow">STAY ORGANIZED</p>
              <h2 id="calendar-agenda-heading">Academic agenda</h2>
            </div>
            <span className="calendar-event-count">
              {sortedEntries.length} {sortedEntries.length === 1 ? "event" : "events"}
            </span>
          </div>

          <ol className="calendar-agenda-list">
            {sortedEntries.map((entry, index) => (
              <li className="calendar-agenda-item" key={`${entry.date}-${entry.title}-${index}`}>
                <div className="calendar-date-marker" aria-hidden="true">
                  <span className="calendar-date-day">{formatDay(entry.date)}</span>
                  <span className="calendar-date-month">{formatMonth(entry.date)}</span>
                </div>

                <article className={`calendar-card calendar-card-${entry.type}`}>
                  <div className="calendar-card-meta">
                    <span className={`calendar-type calendar-type-${entry.type}`}>
                      {typeLabels[entry.type]}
                    </span>

                    {entry.end_date && entry.end_date !== entry.date ? (
                      <span className="calendar-range">
                        <time dateTime={entry.date}>{formatDate(entry.date)}</time>
                        <span aria-hidden="true"> – </span>
                        <span className="sr-only">to</span>
                        <time dateTime={entry.end_date}>{formatDate(entry.end_date)}</time>
                      </span>
                    ) : (
                      <time dateTime={entry.date}>{formatDate(entry.date)}</time>
                    )}
                  </div>

                  <h3>{entry.title}</h3>
                  {entry.description && <p>{entry.description}</p>}
                  {entry.source_url && (
                    <a href={entry.source_url} target="_blank" rel="noopener noreferrer">
                      View official source <span aria-hidden="true">↗</span>
                      <span className="sr-only"> (opens in a new tab)</span>
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
