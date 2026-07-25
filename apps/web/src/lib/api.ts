/**
 * apps/web/src/lib/api.ts
 * ───────────────────────
 * Thin client for apps/api. No hardcoded backend URL: everything goes
 * through NEXT_PUBLIC_API_URL (see .env.example).
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface SourceItem {
  text_snippet: string;
  source: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceItem[];
}

export interface University {
  slug: string;
  name: string;
  locale: string;
  domain: string;
}

/** Thrown when the API is unreachable or returns a non-OK response. */
export class ApiError extends Error {}

function requireApiUrl(): string {
  if (!API_URL) {
    throw new ApiError(
      "NEXT_PUBLIC_API_URL is not set. Copy apps/web/.env.example to apps/web/.env.local and set it.",
    );
  }
  return API_URL;
}

/**
 * Ask a question about a university via POST /chat.
 * Throws ApiError if the request fails (network error, 4xx/5xx response).
 */
export async function sendChatMessage(
  universitySlug: string,
  question: string,
): Promise<ChatResponse> {
  const baseUrl = requireApiUrl();

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ university_slug: universitySlug, question }),
    });
  } catch {
    throw new ApiError(
      `Could not reach the API at ${baseUrl}. Is apps/api running?`,
    );
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body: { detail?: string }) => body.detail)
      .catch(() => undefined);
    throw new ApiError(detail ?? `Request failed with status ${response.status}.`);
  }

  return response.json() as Promise<ChatResponse>;
}

/**
 * List onboarded universities via GET /universities.
 * Throws ApiError if the request fails.
 */
export async function getUniversities(): Promise<University[]> {
  const baseUrl = requireApiUrl();

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/universities`);
  } catch {
    throw new ApiError(
      `Could not reach the API at ${baseUrl}. Is apps/api running?`,
    );
  }

  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}.`);
  }

  return response.json() as Promise<University[]>;
}
