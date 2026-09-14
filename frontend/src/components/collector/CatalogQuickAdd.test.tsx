import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";

import { CatalogQuickAdd } from "./CatalogQuickAdd";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}));

describe("CatalogQuickAdd", () => {
  it("has no accessibility violations", async () => {
    const { container } = render(
      <CatalogQuickAdd onCreate={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it("submits name and tematica", async () => {
    const onCreate = vi.fn();
    render(<CatalogQuickAdd onCreate={onCreate} onCancel={vi.fn()} />);
    await userEvent.type(
      screen.getByLabelText("collector.catalogQuickAdd.name"),
      "Zelda",
    );
    await userEvent.type(
      screen.getByLabelText("collector.catalogQuickAdd.tematica"),
      "Zelda",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "collector.catalogQuickAdd.create" }),
    );
    expect(onCreate).toHaveBeenCalledWith("Zelda", "Zelda");
  });

  it("disables create until both fields filled", () => {
    render(<CatalogQuickAdd onCreate={vi.fn()} onCancel={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: "collector.catalogQuickAdd.create" }),
    ).toBeDisabled();
  });
});
