import "fake-indexeddb/auto";
import { describe, it, expect, beforeEach } from "vitest";
import {
  enqueue,
  listByStatus,
  listAll,
  markApplied,
  markConflict,
  markFailed,
  counts,
  _resetDb,
} from "./queue";
import type { NewQueuedOperation } from "./types";

function op(overrides: Partial<NewQueuedOperation> = {}): NewQueuedOperation {
  return {
    entityType: "collection",
    entityId: "c1",
    method: "PUT",
    endpoint: "/collections/c1",
    body: { name: "x" },
    entityUpdatedAt: null,
    ...overrides,
  };
}

describe("offline queue", () => {
  beforeEach(async () => {
    await _resetDb();
    await new Promise<void>((resolve) => {
      const req = indexedDB.deleteDatabase("hoard-offline");
      req.onsuccess = () => resolve();
      req.onerror = () => resolve();
      req.onblocked = () => resolve();
    });
  });

  it("enqueues with pending status and FIFO ids", async () => {
    const a = await enqueue(op({ endpoint: "/a" }));
    const b = await enqueue(op({ endpoint: "/b" }));
    expect(a.status).toBe("pending");
    expect(b.id).toBeGreaterThan(a.id);
    const pending = await listByStatus("pending");
    expect(pending.map((o) => o.endpoint)).toEqual(["/a", "/b"]);
  });

  it("transitions statuses", async () => {
    const a = await enqueue(op());
    const b = await enqueue(op());
    const c = await enqueue(op());
    await markApplied(a.id);
    await markConflict(b.id);
    await markFailed(c.id, "boom");
    const all = await listAll();
    const byId = Object.fromEntries(all.map((o) => [o.id, o]));
    expect(byId[a.id]!.status).toBe("applied");
    expect(byId[b.id]!.status).toBe("conflict");
    expect(byId[c.id]!.status).toBe("failed");
    expect(byId[c.id]!.error).toBe("boom");
  });

  it("counts by status", async () => {
    const a = await enqueue(op());
    await enqueue(op());
    await markApplied(a.id);
    const c = await counts();
    expect(c.applied).toBe(1);
    expect(c.pending).toBe(1);
  });
});
