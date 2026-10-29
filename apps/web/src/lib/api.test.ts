import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getCalendar,
  getUniversities,
  sendChatMessage,
  type CalendarEntry,
  type ChatResponse,
} from "./api";

const TEST_BASE_URL = "https://api.openuni.test";
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

function textResponse(body: string, init: ResponseInit): Response {
  return new Response(body, init);
}

describe("api client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_URL", TEST_BASE_URL);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  describe("sendChatMessage", () => {
    const chatResponse: ChatResponse = {
      answer: "The deadline is 15 March.",
      sources: [{ text_snippet: "Applications close on 15 March.", source: "https://example.edu/dates" }],
    };

    it("POSTs the question as JSON to {baseUrl}/chat and returns the parsed response", async () => {
      fetchMock.mockResolvedValue(jsonResponse(chatResponse));

      const result = await sendChatMessage("polimi", "When is the deadline?");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(`${TEST_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ university_slug: "polimi", question: "When is the deadline?" }),
      });
      expect(result).toEqual(chatResponse);
    });

    it("falls back to the default base URL when NEXT_PUBLIC_API_URL is not set", async () => {
      vi.stubEnv("NEXT_PUBLIC_API_URL", "");
      fetchMock.mockResolvedValue(jsonResponse(chatResponse));

      await sendChatMessage("polimi", "Hello?");

      expect(fetchMock.mock.calls[0][0]).toBe(`${DEFAULT_BASE_URL}/chat`);
    });

    it("throws the `detail` message from a JSON error body", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ detail: "Unknown university" }, { status: 404 }));

      await expect(sendChatMessage("nope", "Hi")).rejects.toThrow("Unknown university");
    });

    it("throws a status-based message when the error body is not valid JSON", async () => {
      fetchMock.mockResolvedValue(textResponse("<html>Bad Gateway</html>", { status: 502 }));

      await expect(sendChatMessage("polimi", "Hi")).rejects.toThrow("Request failed with status 502");
    });

    it("throws a status-based message when the error body has no `detail`", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ message: "boom" }, { status: 500 }));

      await expect(sendChatMessage("polimi", "Hi")).rejects.toThrow("Request failed with status 500");
    });
  });

  describe("getUniversities", () => {
    it("GETs {baseUrl}/universities and returns the parsed list", async () => {
      const universities = [
        { slug: "polimi", name: "Politecnico di Milano" },
        { slug: "unibo", name: "Università di Bologna" },
      ];
      fetchMock.mockResolvedValue(jsonResponse(universities));

      const result = await getUniversities();

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(`${TEST_BASE_URL}/universities`);
      expect(result).toEqual(universities);
    });

    it("falls back to the default base URL when NEXT_PUBLIC_API_URL is not set", async () => {
      vi.stubEnv("NEXT_PUBLIC_API_URL", "");
      fetchMock.mockResolvedValue(jsonResponse([]));

      await getUniversities();

      expect(fetchMock).toHaveBeenCalledWith(`${DEFAULT_BASE_URL}/universities`);
    });

    it("throws with the status code on a non-OK response", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ detail: "ignored" }, { status: 503 }));

      await expect(getUniversities()).rejects.toThrow("Failed to fetch universities: 503");
    });
  });

  describe("getCalendar", () => {
    const entries: CalendarEntry[] = [
      {
        type: "exam",
        title: "Final exams",
        date: "2026-06-10",
        end_date: "2026-06-24",
        description: null,
        source_url: "https://example.edu/calendar",
      },
    ];

    it("GETs {baseUrl}/universities/{slug}/calendar and returns the parsed entries", async () => {
      fetchMock.mockResolvedValue(jsonResponse(entries));

      const result = await getCalendar("polimi");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(`${TEST_BASE_URL}/universities/polimi/calendar`);
      expect(result).toEqual(entries);
    });

    it("URL-encodes the university slug", async () => {
      fetchMock.mockResolvedValue(jsonResponse([]));

      await getCalendar("uni/bo test?x=1#frag");

      expect(fetchMock).toHaveBeenCalledWith(
        `${TEST_BASE_URL}/universities/uni%2Fbo%20test%3Fx%3D1%23frag/calendar`
      );
    });

    it("throws the `detail` message from a JSON error body", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ detail: "Calendar not found" }, { status: 404 }));

      await expect(getCalendar("nope")).rejects.toThrow("Calendar not found");
    });

    it("throws a status-based message when the error body is not valid JSON", async () => {
      fetchMock.mockResolvedValue(textResponse("Internal Server Error", { status: 500 }));

      await expect(getCalendar("polimi")).rejects.toThrow("Failed to fetch calendar: 500");
    });
  });
});
