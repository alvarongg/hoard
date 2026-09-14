import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ImportPreviewTable } from "./ImportPreviewTable";
import { ImportReport } from "./ImportReport";
import type {
  ImportEntityChange,
  BatchImportResult,
} from "../../types/transfer";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "import.errorRow") return `Row ${opts?.row}`;
      const map: Record<string, string> = {
        "import.empty": "No changes",
        "import.preview": "Preview",
        "import.entity": "Entity",
        "import.action": "Action",
        "import.actions.create": "Create",
        "import.actions.update": "Update",
        "import.actions.skip": "Skip",
        "import.report": "Report",
        "import.toCreate": "To create",
        "import.toUpdate": "To update",
        "import.toSkip": "To skip",
        "import.partialErrors": "Partial errors",
        "table.sortAscending": "Sort ascending",
        "table.sortDescending": "Sort descending",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("ImportPreviewTable", () => {
  const changes: ImportEntityChange[] = [
    {
      entityType: "collection",
      identifier: "My Coll",
      action: "create",
      reason: null,
    },
    {
      entityType: "collection_item",
      identifier: "ci-1",
      action: "skip",
      reason: "already present",
    },
  ];

  it("renders one row per change", () => {
    render(<ImportPreviewTable changes={changes} />);
    expect(screen.getByText("My Coll")).toBeInTheDocument();
    expect(screen.getByText("Create")).toBeInTheDocument();
    expect(screen.getByText("Skip")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<ImportPreviewTable changes={[]} />);
    expect(screen.getByText("No changes")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<ImportPreviewTable changes={changes} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("ImportReport", () => {
  const report: BatchImportResult = {
    createdCount: 3,
    updatedCount: 1,
    skippedCount: 2,
    errorCount: 1,
    errors: [{ row: 4, message: "bad" }],
  };

  it("renders counts and partial errors", () => {
    render(<ImportReport report={report} />);
    expect(screen.getByText(/To create/)).toBeInTheDocument();
    expect(screen.getByText("Partial errors")).toBeInTheDocument();
    expect(screen.getByText(/Row 4/)).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<ImportReport report={report} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
