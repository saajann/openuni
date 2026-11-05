import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getCalendar, getUniversities } from "@/lib/api";
import { demoUniversities, makeCalendarEntry } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

const { replaceMock, searchParams } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  searchParams: { current: new URLSearchParams() },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/calendar",
  useSearchParams: () => searchParams.current,
}));

vi.mock("@/lib/api");

import { CalendarView } from "./calendar-view";

describe("CalendarView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    searchParams.current = new URLSearchParams();
    vi.mocked(getUniversities).mockResolvedValue(demoUniversities);
    vi.mocked(getCalendar).mockResolvedValue([]);
  });

  it("loads the university list and requests the calendar without filters", async () => {
    renderWithProviders(<CalendarView />);

    expect(await screen.findByRole("option", { name: "Demo University" })).toBeInTheDocument();

    await waitFor(() => expect(getCalendar).toHaveBeenCalledWith("demo", {}));
    expect(screen.getByLabelText("Entry type")).toHaveValue("");
    expect(screen.getByLabelText("From")).toHaveValue("");
    expect(screen.getByLabelText("To")).toHaveValue("");
  });

  it("restores filters from the URL and sends them to the API", async () => {
    searchParams.current = new URLSearchParams(
      "type=exam&from=2026-06-01&to=2026-06-30"
    );

    renderWithProviders(<CalendarView />);

    expect(screen.getByLabelText("Entry type")).toHaveValue("exam");
    expect(screen.getByLabelText("From")).toHaveValue("2026-06-01");
    expect(screen.getByLabelText("To")).toHaveValue("2026-06-30");

    await waitFor(() =>
      expect(getCalendar).toHaveBeenCalledWith("demo", {
        type: "exam",
        from: "2026-06-01",
        to: "2026-06-30",
      })
    );
  });

  it("restores the controls when the URL changes outside the component", async () => {
    const { rerender } = renderWithProviders(<CalendarView />);

    await screen.findByRole("option", { name: "Demo University" });

    searchParams.current = new URLSearchParams(
      "type=holiday&from=2026-12-01&to=2026-12-31"
    );
    rerender(<CalendarView />);

    expect(screen.getByLabelText("Entry type")).toHaveValue("holiday");
    expect(screen.getByLabelText("From")).toHaveValue("2026-12-01");
    expect(screen.getByLabelText("To")).toHaveValue("2026-12-31");

    await waitFor(() =>
      expect(getCalendar).toHaveBeenLastCalledWith("demo", {
        type: "holiday",
        from: "2026-12-01",
        to: "2026-12-31",
      })
    );
  });

  it("updates the URL and refetches when filters change", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CalendarView />);

    await screen.findByRole("option", { name: "Demo University" });

    await user.selectOptions(screen.getByLabelText("Entry type"), "deadline");

    expect(replaceMock).toHaveBeenLastCalledWith("/calendar?type=deadline", {
      scroll: false,
    });
    await waitFor(() =>
      expect(getCalendar).toHaveBeenCalledWith("demo", { type: "deadline" })
    );

    fireEvent.change(screen.getByLabelText("From"), {
      target: { value: "2026-05-01" },
    });

    expect(replaceMock).toHaveBeenLastCalledWith(
      "/calendar?type=deadline&from=2026-05-01",
      { scroll: false }
    );
    await waitFor(() =>
      expect(getCalendar).toHaveBeenCalledWith("demo", {
        type: "deadline",
        from: "2026-05-01",
      })
    );
  });

  it("clears every filter and refetches the unfiltered calendar", async () => {
    const user = userEvent.setup();
    searchParams.current = new URLSearchParams("type=exam&from=2026-06-01");

    renderWithProviders(<CalendarView />);

    await screen.findByRole("option", { name: "Demo University" });
    await user.click(screen.getByRole("button", { name: "Clear filters" }));

    expect(replaceMock).toHaveBeenLastCalledWith("/calendar", { scroll: false });
    await waitFor(() => expect(getCalendar).toHaveBeenLastCalledWith("demo", {}));
  });

  it("shows a validation error and skips the request when the range is inverted", async () => {
    searchParams.current = new URLSearchParams("from=2026-06-30&to=2026-06-01");

    renderWithProviders(<CalendarView />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "The start date must be on or before the end date."
    );
    expect(screen.getByLabelText("From")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText("To")).toHaveAttribute("aria-invalid", "true");

    await screen.findByRole("option", { name: "Demo University" });
    expect(getCalendar).not.toHaveBeenCalled();
  });

  it("ignores invalid filter values from the URL", async () => {
    searchParams.current = new URLSearchParams(
      "type=bogus&from=not-a-date&to=2026-02-31"
    );

    renderWithProviders(<CalendarView />);

    expect(screen.getByLabelText("Entry type")).toHaveValue("");
    expect(screen.getByLabelText("From")).toHaveValue("");
    expect(screen.getByLabelText("To")).toHaveValue("");

    await waitFor(() => expect(getCalendar).toHaveBeenCalledWith("demo", {}));
  });

  it("shows the API error and keeps the filters available", async () => {
    vi.mocked(getCalendar).mockRejectedValue(new Error("calendar unavailable"));

    renderWithProviders(<CalendarView />);

    expect(await screen.findByRole("alert")).toHaveTextContent("calendar unavailable");
    expect(screen.getByLabelText("Entry type")).toBeInTheDocument();
  });

  it("renders the returned entries", async () => {
    vi.mocked(getCalendar).mockResolvedValue([
      makeCalendarEntry({ title: "Summer exam", date: "2026-06-15" }),
    ]);

    renderWithProviders(<CalendarView />);

    expect(await screen.findByText("Summer exam")).toBeInTheDocument();
    expect(screen.getByText("June 15, 2026")).toBeInTheDocument();
  });
});
