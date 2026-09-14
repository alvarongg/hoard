import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}));

const resolveMutate = vi.fn();
const mockPending = vi.fn();

vi.mock("../hooks/useCollectorWorkflow", () => ({
  usePending: () => mockPending(),
}));

import { PendingPage } from "./PendingPage";

describe("PendingPage", () => {
  it("shows empty state when no pending", () => {
    mockPending.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      resolve: { mutate: resolveMutate },
    });
    render(<PendingPage />);
    expect(screen.getByText("pending.empty")).toBeInTheDocument();
  });

  it("lists pending grouped and resolves a field", async () => {
    mockPending.mockReturnValue({
      data: [
        {
          id: "p1",
          entityType: "supplier",
          entityId: "s1",
          missingFields: ["country"],
          status: "open",
          createdAt: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
      isError: false,
      resolve: { mutate: resolveMutate },
    });
    render(<PendingPage />);
    expect(screen.getByText("pending.entity.supplier")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "pending.markDone" }),
    );
    expect(resolveMutate).toHaveBeenCalledWith({
      id: "p1",
      completedFields: ["country"],
    });
  });

  it("has no accessibility violations", async () => {
    mockPending.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      resolve: { mutate: resolveMutate },
    });
    const { container } = render(<PendingPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
