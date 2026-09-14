import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useAnnouncement, AnnouncementProvider } from "./useAnnouncement";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// Test component that uses the announcement hook
function TestComponent({
  message,
  politeness,
}: {
  message: string;
  politeness?: "polite" | "assertive";
}) {
  const announce = useAnnouncement();
  return (
    <button onClick={() => announce(message, politeness)}>Announce</button>
  );
}

describe("useAnnouncement", () => {
  it("throws error when used outside of AnnouncementProvider", () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      render(<TestComponent message="test" />);
        }).toThrow("useAnnouncement must be used within an AnnouncementProvider");

    consoleSpy.mockRestore();
  });

  it("announces a polite message by default", async () => {
    const user = userEvent.setup();

    render(
      <AnnouncementProvider>
        <TestComponent message="Item saved successfully" />
      </AnnouncementProvider>
    );

    await user.click(screen.getByRole("button", { name: "Announce" }));

    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("Item saved successfully");
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
    expect(liveRegion).toHaveAttribute("aria-atomic", "true");
  });

  it("announces an assertive message when specified", async () => {
    const user = userEvent.setup();

    render(
      <AnnouncementProvider>
        <TestComponent message="Error saving item" politeness="assertive" />
      </AnnouncementProvider>
    );

    await user.click(screen.getByRole("button", { name: "Announce" }));

    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("Error saving item");
    expect(liveRegion).toHaveAttribute("aria-live", "assertive");
  });

  it("re-announces identical messages", async () => {
    const user = userEvent.setup();

    render(
      <AnnouncementProvider>
        <TestComponent message="Same message" />
      </AnnouncementProvider>
    );

    // First announcement
    await user.click(screen.getByRole("button", { name: "Announce" }));
    let liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("Same message");

    // Second identical announcement should still work
    await user.click(screen.getByRole("button", { name: "Announce" }));
    liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("Same message");
  });

  it("does not render anything when no announcement has been made", () => {
    render(
      <AnnouncementProvider>
        <div>No announcement yet</div>
      </AnnouncementProvider>
    );

    // No live region should be rendered
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("renders live region with sr-only class for visual hiding", async () => {
    const user = userEvent.setup();

    render(
      <AnnouncementProvider>
        <TestComponent message="Hidden message" />
      </AnnouncementProvider>
    );

    await user.click(screen.getByRole("button", { name: "Announce" }));

    const liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveClass("sr-only");
  });

  it("has no accessibility violations", async () => {
    const user = userEvent.setup();

    const { container } = render(
      <AnnouncementProvider>
        <TestComponent message="Accessible message" />
      </AnnouncementProvider>
    );

    await user.click(screen.getByRole("button", { name: "Announce" }));

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("can be called multiple times with different messages", async () => {
    function MultipleAnnouncements() {
      const announce = useAnnouncement();
      return (
        <div>
          <button onClick={() => announce("First message")}>First</button>
          <button onClick={() => announce("Second message", "assertive")}>Second</button>
        </div>
      );
    }

    const user = userEvent.setup();

    render(
      <AnnouncementProvider>
        <MultipleAnnouncements />
      </AnnouncementProvider>
    );

    await user.click(screen.getByRole("button", { name: "First" }));
    let liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("First message");
    expect(liveRegion).toHaveAttribute("aria-live", "polite");

    await user.click(screen.getByRole("button", { name: "Second" }));
    liveRegion = screen.getByRole("status");
    expect(liveRegion).toHaveTextContent("Second message");
    expect(liveRegion).toHaveAttribute("aria-live", "assertive");
  });
});
