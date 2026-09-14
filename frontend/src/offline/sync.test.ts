import "fake-indexeddb/auto";
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { enqueue, listByStatus, _resetDb } from "./queue";
import { drainQueue } from "./sync";
import type { NewQueuedOperation } from "./types";

function op(overrides: Partial<NewQueuedOperation> = {}): NewQueuedOperation {
  return {
    entityType: "collection",
    entityId: null,
    method: "POST",
    endpoint: "/collections",
    body: { name: "x" },
    entityUpdatedAt: null,
    ...overrides,
  };
}

function okResponse(): Response {
  return { ok: true, status: 201, json: async () => ({}) } as Response;
}
function statusResponse(status: number): Response {
  return { ok: false, status, json: async () => ({}) } as Response;
}

describe("drainQueue", () => {
  beforeEach(async () => {
    await _resetDb();
    await new Promise<void>((resolve) => {
      const req = indexedDB.deleteDatabase("hoard-offline");
      req.onsuccess = () => resolve();
      req.onerror = () => resolve();
      req.onblocked = () => resolve();
    });
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  it("empty queue is a no-op", async () => {
    const result = await drainQueue();
    expect(result.applied).toBe(0);
  });

  it("applies all pending operations in order", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(okResponse());
    await enqueue(op({ endpoint: "/a" }));
    await enqueue(op({ endpoint: "/b" }));
    const result = await drainQueue();
    expect(result.applied).toBe(2);
    expect(await listByStatus("pending")).toHaveLength(0);
    expect(await listByStatus("applied")).toHaveLength(2);
  });

  it("422 marks failed without retry", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(statusResponse(422));
    await enqueue(op());
    const result = await drainQueue();
    expect(result.failed).toBe(1);
    expect(await listByStatus("failed")).toHaveLength(1);
  });

  it("network error mid-drain leaves the rest pending", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(okResponse())
      .mockRejectedValueOnce(new Error("network"));
    await enqueue(op({ endpoint: "/a" }));
    await enqueue(op({ endpoint: "/b" }));
    const result = await drainQueue();
    expect(result.applied).toBe(1);
    expect(await listByStatus("pending")).toHaveLength(1);
  });

  it("marks conflict when server updatedAt is newer than enqueue time", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    // GET returns a newer updatedAt than captured.
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ updatedAt: "2030-01-01T00:00:00Z" }),
    } as Response);
    await enqueue(
      op({
        method: "PUT",
        entityId: "c1",
        endpoint: "/collections/c1",
        entityUpdatedAt: "2020-01-01T00:00:00Z",
      }),
    );
    const result = await drainQueue();
    expect(result.conflicts).toBe(1);
    expect(await listByStatus("conflict")).toHaveLength(1);
    // Only the GET was issued, no PUT.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
