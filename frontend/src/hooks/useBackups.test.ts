import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useBackups, useBackupConfig } from "./useBackups";

const API_URL = "http://localhost:8000/api";

describe("useBackups", () => {
  it("lists backups", async () => {
    server.use(
      http.get(`${API_URL}/backups`, () =>
        HttpResponse.json([
          {
            id: "b1",
            filename: "b1.tar.gz",
            created_at: "2026-01-01T00:00:00Z",
            size_bytes: 100,
            trigger: "manual",
          },
        ]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useBackups(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.filename).toBe("b1.tar.gz");
  });

  it("surfaces 503 on create when pg_dump is unavailable", async () => {
    server.use(
      http.get(`${API_URL}/backups`, () => HttpResponse.json([])),
      http.post(`${API_URL}/backups`, () =>
        HttpResponse.json({ detail: "pg_dump is not available" }, { status: 503 }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useBackups(), { wrapper });
    await result.current.create.mutateAsync().catch(() => undefined);
    await waitFor(() =>
      expect(result.current.create.isError).toBe(true),
    );
  });
});

describe("useBackupConfig", () => {
  it("reads config", async () => {
    server.use(
      http.get(`${API_URL}/backups/config`, () =>
        HttpResponse.json({
          frequency: "weekly",
          retention_count: 7,
          next_run_at: null,
          last_run_at: null,
          last_run_status: null,
        }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useBackupConfig(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.retentionCount).toBe(7);
  });
});
