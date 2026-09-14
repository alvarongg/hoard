import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { LiveRegion } from "./LiveRegion";

expect.extend(toHaveNoViolations);

describe("LiveRegion", () => {
  it("renders with role=status for screen readers", () => {
    render(<LiveRegion message="Item added successfully" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("announces the message content", () => {
    render(<LiveRegion message="Changes saved" />);
    expect(screen.getByRole("status")).toHaveTextContent("Changes saved");
  });

  it("uses aria-live=polite by default", () => {
    render(<LiveRegion message="Polite announcement" />);
    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
  });

  it("supports assertive politeness for critical messages", () => {
    render(<LiveRegion message="Critical error!" politeness="assertive" />);
    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveAttribute("aria-live", "assertive");
  });

  it("has aria-atomic=true for complete announcement", () => {
    render(<LiveRegion message="Atomic message" />);
    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveAttribute("aria-atomic", "true");
  });

  it("is visually hidden with sr-only class", () => {
    render(<LiveRegion message="Hidden from sight" />);
    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveClass("sr-only");
  });

  it("announces empty message without errors", () => {
    render(<LiveRegion message="" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("handles long messages", () => {
    const longMessage = "This is a very long message that might be used to announce detailed information to screen reader users. It should still work correctly and be announced completely.";
    render(<LiveRegion message={longMessage} />);
    expect(screen.getByRole("status")).toHaveTextContent(longMessage);
  });

  it("has no accessibility violations with polite message", async () => {
    const { container } = render(
      <LiveRegion message="Accessible polite message" />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with assertive message", async () => {
    const { container } = render(
      <LiveRegion message="Accessible assertive message" politeness="assertive" />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
