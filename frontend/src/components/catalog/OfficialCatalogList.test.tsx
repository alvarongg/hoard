import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OfficialCatalogList } from "./OfficialCatalogList";
import { catalogLibraryApi } from "../../services/catalogLibraryApi";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) =>
      opts ? `${key} ${JSON.stringify(opts)}` : key,
  }),
}));

vi.mock("../../services/catalogLibraryApi", () => ({
  catalogLibraryApi: {
    manifest: vi.fn(),
    load: vi.fn(),
  },
}));

function renderList() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <OfficialCatalogList />
    </QueryClientProvider>,
  );
}

const manifest = {
  schemaVersion: "1.0",
  catalogs: [
    {
      id: "nes",
      name: "NES",
      system: "nes",
      version: "1.0.0",
      itemCount: 1208,
      path: "nes.v1.json",
    },
  ],
};

describe("OfficialCatalogList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders catalogs from the manifest", async () => {
    vi.mocked(catalogLibraryApi.manifest).mockResolvedValue(manifest);
    renderList();
    expect(await screen.findByText("NES")).toBeInTheDocument();
  });

  it("loads a catalog and shows the result", async () => {
    vi.mocked(catalogLibraryApi.manifest).mockResolvedValue(manifest);
    vi.mocked(catalogLibraryApi.load).mockResolvedValue({
      createdCount: 1208,
      updatedCount: 0,
      skippedCount: 0,
      errorCount: 0,
    });
    renderList();
    const btn = await screen.findByText("catalogLibrary.load");
    await userEvent.click(btn);
    await waitFor(() =>
      expect(catalogLibraryApi.load).toHaveBeenCalledWith("nes"),
    );
    expect(
      await screen.findByText(/catalogLibrary.loaded/),
    ).toBeInTheDocument();
  });

  it("shows an error when loading fails", async () => {
    vi.mocked(catalogLibraryApi.manifest).mockResolvedValue(manifest);
    vi.mocked(catalogLibraryApi.load).mockRejectedValue(
      new Error("checksum mismatch"),
    );
    renderList();
    const btn = await screen.findByText("catalogLibrary.load");
    await userEvent.click(btn);
    expect(
      await screen.findByText("catalogLibrary.loadError"),
    ).toBeInTheDocument();
  });

  it("shows empty state when there are no catalogs", async () => {
    vi.mocked(catalogLibraryApi.manifest).mockResolvedValue({
      schemaVersion: "1.0",
      catalogs: [],
    });
    renderList();
    expect(
      await screen.findByText("catalogLibrary.empty"),
    ).toBeInTheDocument();
  });
});
