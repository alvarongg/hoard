import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { CompletenessBadge } from "./CompletenessBadge";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "components.complete": "Complete",
        "components.incomplete": `Incomplete (${params?.present ?? ""}/${params?.required ?? ""})`,
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("CompletenessBadge", () => {
  it("renders the complete label when the item is complete", () => {
    render(
      <CompletenessBadge isComplete presentCount={3} requiredCount={3} />,
    );

    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("exposes the badge as a status region", () => {
    render(
      <CompletenessBadge isComplete presentCount={3} requiredCount={3} />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Complete");
  });

  it("renders the incomplete label with present and required counts", () => {
    render(
      <CompletenessBadge
        isComplete={false}
        presentCount={2}
        requiredCount={5}
      />,
    );

    expect(screen.getByText("Incomplete (2/5)")).toBeInTheDocument();
  });

  it("has no accessibility violations when complete", async () => {
    const { container } = render(
      <CompletenessBadge isComplete presentCount={4} requiredCount={4} />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations when incomplete", async () => {
    const { container } = render(
      <CompletenessBadge
        isComplete={false}
        presentCount={1}
        requiredCount={4}
      />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
