import type { Metadata } from "next";
import { Suspense } from "react";

import { CalendarView } from "@/components/calendar-view";

export const metadata: Metadata = {
  title: "Academic Calendar",
  description:
    "Browse exams, deadlines, holidays and university events in chronological order.",
};

function CalendarFallback() {
  return (
    <main id="main-content" className="container" tabIndex={-1}>
      <div className="loading-container" role="status">
        <div className="spinner" aria-hidden="true"></div>
        <p>Loading academic calendar...</p>
      </div>
    </main>
  );
}

export default function CalendarPage() {
  return (
    <Suspense fallback={<CalendarFallback />}>
      <CalendarView />
    </Suspense>
  );
}
