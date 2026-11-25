import { act, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getUniversities, sendChatMessage, type ChatResponse } from "@/lib/api";

import { ChatWorkspace } from "@/components/chat-workspace";
import { demoUniversities, makeChatResponse } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

vi.mock("@/lib/api");

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });

  return { promise, resolve };
}

describe("ChatWorkspace", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(getUniversities).mockResolvedValue(demoUniversities);
  });

  it("renders labelled controls and loads the university list", async () => {
    renderWithProviders(<ChatWorkspace />);

    expect(screen.getByRole("heading", { level: 1, name: "OpenUni" })).toBeInTheDocument();
    expect(screen.getByLabelText("University")).toBeInTheDocument();
    expect(screen.getByLabelText("What do you want to know?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask Question" })).toBeDisabled();

    expect(await screen.findByRole("option", { name: "Demo University" })).toBeInTheDocument();
  });

  it("falls back to the demo university when the list request fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(getUniversities).mockRejectedValue(new Error("api down"));

    renderWithProviders(<ChatWorkspace />);

    expect(await screen.findByRole("option", { name: "Demo University" })).toBeInTheDocument();
  });

  it("shows the api error when a chat request fails", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage).mockRejectedValue(new Error("provider unavailable"));

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    expect(await screen.findByText("provider unavailable")).toBeInTheDocument();
  });

  it("offers a retry action and resubmits the failed request", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(new Error("provider unavailable"))
      .mockResolvedValueOnce(makeChatResponse());

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("provider unavailable");

    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(sendChatMessage).toHaveBeenCalledTimes(2);
    expect(sendChatMessage).toHaveBeenNthCalledWith(1, "demo", "When is the exam?");
    expect(sendChatMessage).toHaveBeenNthCalledWith(2, "demo", "When is the exam?");
  });

  it("retries the failed pair even after the form changes", async () => {
    const user = userEvent.setup();
    vi.mocked(getUniversities).mockResolvedValue([
      ...demoUniversities,
      { slug: "other", name: "Other University" },
    ]);
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(new Error("provider unavailable"))
      .mockResolvedValueOnce(makeChatResponse());

    renderWithProviders(<ChatWorkspace />);

    const questionInput = screen.getByLabelText("What do you want to know?");
    await user.type(questionInput, "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    await screen.findByRole("button", { name: "Try again" });
    await screen.findByRole("option", { name: "Other University" });

    await user.selectOptions(screen.getByLabelText("University"), "other");
    await user.clear(questionInput);
    await user.type(questionInput, "A different question");

    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(sendChatMessage).toHaveBeenNthCalledWith(2, "demo", "When is the exam?");
  });

  it("clears the error and disables the form while a retry is in flight", async () => {
    const user = userEvent.setup();
    const pending = deferred<ChatResponse>();
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(new Error("provider unavailable"))
      .mockReturnValueOnce(pending.promise);

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));
    await screen.findByRole("button", { name: "Try again" });

    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText("Analyzing university documents...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Searching..." })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();

    await act(async () => {
      pending.resolve(makeChatResponse());
      await pending.promise;
    });

    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
  });

  it("renders a grounded answer and its sources", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage).mockResolvedValue(makeChatResponse());

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(screen.getByText("The exam is in June.")).toBeInTheDocument();
    expect(screen.getByText("calendar.pdf")).toBeInTheDocument();
    expect(screen.getByText("1 source cited")).toBeInTheDocument();
    expect(sendChatMessage).toHaveBeenCalledWith("demo", "When is the exam?");
  });

  it("renders answers as text, preserving newlines without injecting HTML", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage).mockResolvedValue(
      makeChatResponse({
        answer:
          "Use <strong>official</strong> sources.\nKeep this on the same line.\n\nSecond paragraph.",
        sources: [],
      })
    );

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "Where do I check?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    const answer = await screen.findByTestId("answer-text");
    expect(answer.querySelector("strong")).toBeNull();

    const paragraphs = answer.querySelectorAll("p");
    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0].textContent).toBe(
      "Use <strong>official</strong> sources.\nKeep this on the same line."
    );
    expect(paragraphs[1].textContent).toBe("Second paragraph.");
  });

  it("shows an explicit empty state when no sources are returned", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage).mockResolvedValue(makeChatResponse({ sources: [] }));

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    expect(
      await screen.findByText("No supporting sources were returned for this answer.")
    ).toBeInTheDocument();
    expect(screen.getByText("No sources cited")).toBeInTheDocument();
  });

  it("renders every source without inventing external links", async () => {
    const user = userEvent.setup();
    vi.mocked(sendChatMessage).mockResolvedValue(
      makeChatResponse({
        sources: [
          { text_snippet: "Exams run in June.", source: "calendar.pdf" },
          { text_snippet: "Deadlines are in May.", source: "deadlines.pdf" },
        ],
      })
    );

    renderWithProviders(<ChatWorkspace />);

    await user.type(screen.getByLabelText("What do you want to know?"), "When is the exam?");
    await user.click(screen.getByRole("button", { name: "Ask Question" }));

    expect(await screen.findByText("calendar.pdf")).toBeInTheDocument();
    expect(screen.getByText("deadlines.pdf")).toBeInTheDocument();
    expect(screen.getByText("Exams run in June.")).toBeInTheDocument();
    expect(screen.getByText("Deadlines are in May.")).toBeInTheDocument();
    expect(screen.getByText("2 sources cited")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "calendar.pdf" })).not.toBeInTheDocument();
  });
});
