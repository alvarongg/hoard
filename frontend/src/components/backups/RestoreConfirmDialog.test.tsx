import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { RestoreConfirmDialog } from "./RestoreConfirmDialog";
import { BackupList } from "./BackupList";
import type { BackupInfo } from "../../types/backup";

expect.extend(toHaveNoViolations);

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

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "backups.restoreWarning")
        return `Restoring ${opts?.filename} is irreversible`;
      if (key === "backups.restoreConfirmPrompt")
        return `Type ${opts?.word} to confirm`;
      const map: Record<string, string> = {
        "backups.restore": "Restore",
        "backups.restoreConfirmWord": "RESTORE",
        "backups.title": "Backups",
        "backups.empty": "No backups",
        "backups.createdAt": "Date",
        "backups.size": "Size",
        "backups.download": "Download",
        "common.cancel": "Cancel",
        "common.delete": "Delete",
        "common.actions": "Actions",
        "table.sortAscending": "Sort ascending",
        "table.sortDescending": "Sort descending",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("RestoreConfirmDialog", () => {
  it("keeps restore disabled until the confirmation word is typed", async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(
      <RestoreConfirmDialog
        isOpen
        filename="backup.tar.gz"
        onClose={vi.fn()}
        onConfirm={onConfirm}
        isLoading={false}
      />,
    );
    const restoreBtn = screen.getByRole("button", { name: "Restore" });
    expect(restoreBtn).toBeDisabled();

    await user.type(screen.getByLabelText(/Type RESTORE/), "RESTORE");
    expect(restoreBtn).toBeEnabled();
    await user.click(restoreBtn);
    expect(onConfirm).toHaveBeenCalled();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <RestoreConfirmDialog
        isOpen
        filename="b.tar.gz"
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isLoading={false}
      />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("BackupList", () => {
  const backups: BackupInfo[] = [
    {
      id: "b1",
      filename: "hoard-backup-1.tar.gz",
      createdAt: "2026-03-01T00:00:00Z",
      sizeBytes: 2048,
      trigger: "manual",
    },
  ];

  it("renders backups and triggers actions", async () => {
    const onDownload = vi.fn();
    const onRestore = vi.fn();
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(
      <BackupList
        backups={backups}
        onDownload={onDownload}
        onRestore={onRestore}
        onDelete={onDelete}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Download" }));
    expect(onDownload).toHaveBeenCalledWith("b1");
    await user.click(screen.getByRole("button", { name: "Restore" }));
    expect(onRestore).toHaveBeenCalledWith(backups[0]);
  });

  it("shows empty state", () => {
    render(
      <BackupList
        backups={[]}
        onDownload={vi.fn()}
        onRestore={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("No backups")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <BackupList
        backups={backups}
        onDownload={vi.fn()}
        onRestore={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
