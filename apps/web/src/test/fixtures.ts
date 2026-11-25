import type { CalendarEntry, ChatResponse } from "@/lib/api";

export const demoUniversities = [{ slug: "demo", name: "Demo University" }];

export function makeChatResponse(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    answer: "The exam is in June.",
    sources: [{ text_snippet: "Exams run in June.", source: "calendar.pdf" }],
    ...overrides,
  };
}

export function makeCalendarEntry(overrides: Partial<CalendarEntry> = {}): CalendarEntry {
  return {
    type: "exam",
    title: "Summer exam",
    date: "2026-06-15",
    end_date: null,
    description: null,
    source_url: null,
    ...overrides,
  };
}
