import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { usePathnameMock } = vi.hoisted(() => ({
  usePathnameMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: usePathnameMock,
}));

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  beforeEach(() => {
    usePathnameMock.mockReset();
    usePathnameMock.mockReturnValue("/");
  });

  it("links to both routes inside the primary navigation", () => {
    render(<SiteHeader />);

    const navigation = screen.getByRole("navigation", { name: "Primary" });
    expect(navigation).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Calendar" })).toHaveAttribute("href", "/calendar");
  });

  it("marks the current route programmatically and visually", () => {
    usePathnameMock.mockReturnValue("/calendar");
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Calendar" })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("link", { name: "Ask" })).not.toHaveAttribute("aria-current");
  });

  it("keeps the home route active only on the exact root path", () => {
    usePathnameMock.mockReturnValue("/calendar");
    const { rerender } = render(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Ask" })).not.toHaveAttribute("aria-current");

    usePathnameMock.mockReturnValue("/");
    rerender(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Calendar" })).not.toHaveAttribute("aria-current");
  });

  it("makes both navigation links reachable by keyboard", async () => {
    const user = userEvent.setup();
    render(<SiteHeader />);

    await user.tab();
    expect(screen.getByRole("link", { name: "OpenUni home" })).toHaveFocus();

    await user.tab();
    expect(screen.getByRole("link", { name: "Ask" })).toHaveFocus();

    await user.tab();
    expect(screen.getByRole("link", { name: "Calendar" })).toHaveFocus();
  });
});
