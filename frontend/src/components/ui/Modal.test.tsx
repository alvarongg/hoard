import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Modal } from "./Modal";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "ui.close": "Close",
      };
      return translations[key] ?? key;
    },
  }),
}));

beforeAll(() => {
  HTMLDialogElement.prototype.showModal =
    HTMLDialogElement.prototype.showModal ||
    function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    };
  HTMLDialogElement.prototype.close =
    HTMLDialogElement.prototype.close ||
    function (this: HTMLDialogElement) {
      this.removeAttribute("open");
    };
});

describe("Modal", () => {
  it("renders nothing when closed", () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    expect(screen.queryByText("Content")).not.toBeInTheDocument();
  });

  it("renders content when open", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test Modal">
        Modal content
      </Modal>,
    );
    expect(screen.getByText("Modal content")).toBeInTheDocument();
  });

  it("renders title as heading", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="My Title">
        Content
      </Modal>,
    );
    expect(screen.getByRole("heading", { name: "My Title" })).toBeInTheDocument();
  });

  it("has aria-modal attribute on dialog", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("has aria-labelledby linking to title", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-labelledby", "modal-title");
  });

  it("renders close button with aria-label", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test">
        Content
      </Modal>,
    );
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls onClose when Escape is pressed", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test">
        Content
      </Modal>,
    );
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()} title="Accessible Modal">
        Content
      </Modal>,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
