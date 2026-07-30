export interface SourceItem {
  text_snippet: string;
  source: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceItem[];
}

export async function sendChatMessage(
  university: string,
  question: string
): Promise<ChatResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const res = await fetch(`${baseUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ university_slug: university, question }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}
