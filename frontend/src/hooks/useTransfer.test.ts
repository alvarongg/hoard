import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { createWrapper } from "../test/hookWrapper";
import { useJsonImport } from "./useTransfer";

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => body,
    blob: async () => new Blob([JSON.stringify(body)]),
  } as unknown as Response;
}

describe("useJsonImport", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("previews then executes, moving through steps", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          schema_version: "1.0",
          to_create: 2,
          to_update: 0,
          to_skip: 0,
          changes: [],
          errors: [],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          created_count: 2,
          updated_count: 0,
          skipped_count: 0,
          error_count: 0,
          errors: [],
        }),
      );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useJsonImport(), { wrapper });

    const file = new File(["{}"], "export.json", {
      type: "application/json",
    });

    act(() => result.current.selectFile(file));
    await waitFor(() => expect(result.current.step).toBe("preview"));
    expect(result.current.preview?.toCreate).toBe(2);

    act(() => result.current.confirm());
    await waitFor(() => expect(result.current.step).toBe("report"));
    expect(result.current.report?.createdCount).toBe(2);
  });

  it("cancel resets without executing", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        schema_version: "1.0",
        to_create: 1,
        to_update: 0,
        to_skip: 0,
        changes: [],
        errors: [],
      }),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useJsonImport(), { wrapper });
    const file = new File(["{}"], "export.json");

    act(() => result.current.selectFile(file));
    await waitFor(() => expect(result.current.step).toBe("preview"));

    act(() => result.current.cancel());
    expect(result.current.step).toBe("upload");
    expect(result.current.preview).toBeNull();
    // execute endpoint never called (only the preview fetch happened)
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
