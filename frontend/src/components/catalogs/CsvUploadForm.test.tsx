import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { http, HttpResponse } from "msw";
import { CsvUploadForm } from "./CsvUploadForm";
import { createWrapper } from "../../test/hookWrapper";
import { server } from "../../test/mocks/server";
import type { BatchImportResult } from "../../types/catalog";

expect.extend(toHaveNoViolations);

const API_URL = "http://localhost:8000/api";
const CATALOG_ID = "catalog-1";
const MAX_FILE_SIZE = 5 * 1024 * 1024;

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "catalogs.csv.upload": "Import CSV",
        "catalogs.csv.selectFile": "CSV file",
        "catalogs.csv.importing": "Importing...",
        "catalogs.csv.importComplete": "Import complete",
        "catalogs.csv.createdCount": `Created items: ${options?.count}`,
        "catalogs.csv.errorCount": `Rows with errors: ${options?.count}`,
        "catalogs.csv.errorDetail": `Row ${options?.row}: ${options?.message}`,
        "catalogs.csv.fileTooLarge": "The file exceeds the 5 MB limit",
        "catalogs.csv.invalidFileType": "Only .csv files are allowed",
        "catalogs.csv.noData": "The file has no data rows",
        "common.cancel": "Cancel",
        "common.loading": "Loading...",
      };
      return translations[key] ?? key;
    },
  }),
}));

function renderForm(overrides: { onImportComplete?: ReturnType<typeof vi.fn> } = {}) {
  const onImportComplete = overrides.onImportComplete ?? vi.fn();
  const onCancel = vi.fn();
  const { wrapper } = createWrapper();

  const result = render(
    <CsvUploadForm
      catalogId={CATALOG_ID}
      onImportComplete={onImportComplete}
      onCancel={onCancel}
    />,
    { wrapper },
  );

  return { ...result, onImportComplete, onCancel };
}

function csvFile(name = "items.csv", type = "text/csv"): File {
  return new File(["title\nSuper Mario 64\n"], name, { type });
}

/** jsdom cannot allocate a real 5 MB file cheaply, so the size is stubbed. */
function oversizedCsvFile(): File {
  const file = csvFile("huge.csv");
  Object.defineProperty(file, "size", { value: MAX_FILE_SIZE + 1 });
  return file;
}

function mockImport(result: {
  created_count: number;
  error_count: number;
  errors: { row: number; message: string }[];
}) {
  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/import-csv`, () =>
      HttpResponse.json(result),
    ),
  );
}

function mockImportFailure() {
  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/import-csv`, () =>
      HttpResponse.json({ detail: "Catalog not found" }, { status: 404 }),
    ),
  );
}

describe("CsvUploadForm", () => {
  it("renders the file input with the correct label", () => {
    renderForm();

    const input = screen.getByLabelText("CSV file");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("type", "file");
    expect(input).toHaveAttribute("accept", ".csv");
  });

  it("keeps the upload button disabled until a valid file is selected", async () => {
    const user = userEvent.setup();
    renderForm();

    const uploadButton = screen.getByRole("button", { name: "Import CSV" });
    expect(uploadButton).toBeDisabled();

    await user.upload(screen.getByLabelText("CSV file"), csvFile());

    expect(uploadButton).toBeEnabled();
  });

  it("rejects non-CSV files", async () => {
    renderForm();

    // fireEvent bypasses the browser-level `accept` filter, exercising the
    // component's own validation the way a drag-and-drop would.
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [new File(["nope"], "items.txt", { type: "text/plain" })] },
    });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Only .csv files are allowed",
    );
    expect(screen.getByLabelText("CSV file")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(screen.getByRole("button", { name: "Import CSV" })).toBeDisabled();
  });

  it("rejects files larger than 5 MB", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.upload(screen.getByLabelText("CSV file"), oversizedCsvFile());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The file exceeds the 5 MB limit",
    );
    expect(screen.getByRole("button", { name: "Import CSV" })).toBeDisabled();
  });

  it("shows the result summary after a successful import", async () => {
    mockImport({ created_count: 3, error_count: 0, errors: [] });
    const user = userEvent.setup();
    const { onImportComplete } = renderForm();

    await user.upload(screen.getByLabelText("CSV file"), csvFile());
    await user.click(screen.getByRole("button", { name: "Import CSV" }));

    expect(await screen.findByText("Import complete")).toBeInTheDocument();
    expect(screen.getByText("Created items: 3")).toBeInTheDocument();
    expect(screen.getByText("Rows with errors: 0")).toBeInTheDocument();

    const expected: BatchImportResult = {
      createdCount: 3,
      errorCount: 0,
      errors: [],
    };
    expect(onImportComplete).toHaveBeenCalledWith(expected);
  });

  it("shows per-row errors when the import reports them", async () => {
    mockImport({
      created_count: 1,
      error_count: 2,
      errors: [
        { row: 3, message: "Missing title" },
        { row: 7, message: "Title too long" },
      ],
    });
    const user = userEvent.setup();
    renderForm();

    await user.upload(screen.getByLabelText("CSV file"), csvFile());
    await user.click(screen.getByRole("button", { name: "Import CSV" }));

    expect(await screen.findByText("Import complete")).toBeInTheDocument();
    expect(screen.getByText("Created items: 1")).toBeInTheDocument();
    expect(screen.getByText("Row 3: Missing title")).toBeInTheDocument();
    expect(screen.getByText("Row 7: Title too long")).toBeInTheDocument();
  });

  it("reports an empty file with no data rows", async () => {
    mockImport({ created_count: 0, error_count: 0, errors: [] });
    const user = userEvent.setup();
    renderForm();

    await user.upload(screen.getByLabelText("CSV file"), csvFile("empty.csv"));
    await user.click(screen.getByRole("button", { name: "Import CSV" }));

    expect(
      await screen.findByText("The file has no data rows"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Created items: 0")).not.toBeInTheDocument();
  });

  it("shows an error message when the import request fails", async () => {
    mockImportFailure();
    const user = userEvent.setup();
    const { onImportComplete } = renderForm();

    await user.upload(screen.getByLabelText("CSV file"), csvFile());
    await user.click(screen.getByRole("button", { name: "Import CSV" }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.queryByText("Import complete")).not.toBeInTheDocument();
    expect(onImportComplete).not.toHaveBeenCalled();
  });

  it("calls onCancel when the cancel button is clicked", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderForm();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("has no accessibility violations", async () => {
    const { container } = renderForm();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations while showing import results", async () => {
    mockImport({
      created_count: 1,
      error_count: 1,
      errors: [{ row: 2, message: "Missing title" }],
    });
    const user = userEvent.setup();
    const { container } = renderForm();

    await user.upload(screen.getByLabelText("CSV file"), csvFile());
    await user.click(screen.getByRole("button", { name: "Import CSV" }));
    await screen.findByText("Import complete");

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
