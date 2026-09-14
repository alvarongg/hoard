import { openDB, type IDBPDatabase } from "idb";
import type {
  QueuedOperation,
  QueuedStatus,
  NewQueuedOperation,
} from "./types";

const DB_NAME = "hoard-offline";
const STORE = "operations";

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, 1, {
      upgrade(db) {
        const store = db.createObjectStore(STORE, {
          keyPath: "id",
          autoIncrement: true,
        });
        store.createIndex("status", "status");
      },
    });
  }
  return dbPromise;
}

/** Reset the cached connection (test helper). */
export async function _resetDb(): Promise<void> {
  if (dbPromise) {
    try {
      const db = await dbPromise;
      db.close();
    } catch {
      /* ignore */
    }
    dbPromise = null;
  }
}

export async function enqueue(
  op: NewQueuedOperation,
): Promise<QueuedOperation> {
  const db = await getDb();
  const record: Omit<QueuedOperation, "id"> = {
    ...op,
    status: "pending",
    attempts: 0,
    error: null,
    createdAt: Date.now(),
  };
  const id = (await db.add(STORE, record)) as number;
  return { ...record, id };
}

export async function listByStatus(
  status: QueuedStatus,
): Promise<QueuedOperation[]> {
  const db = await getDb();
  const all = (await db.getAllFromIndex(
    STORE,
    "status",
    status,
  )) as QueuedOperation[];
  return all.sort((a, b) => a.id - b.id);
}

export async function listAll(): Promise<QueuedOperation[]> {
  const db = await getDb();
  const all = (await db.getAll(STORE)) as QueuedOperation[];
  return all.sort((a, b) => a.id - b.id);
}

async function setStatus(
  id: number,
  status: QueuedStatus,
  patch: Partial<QueuedOperation> = {},
): Promise<void> {
  const db = await getDb();
  const existing = (await db.get(STORE, id)) as QueuedOperation | undefined;
  if (!existing) return;
  await db.put(STORE, { ...existing, ...patch, status });
}

export const markApplied = (id: number) => setStatus(id, "applied");
export const markConflict = (id: number) => setStatus(id, "conflict");
export const markFailed = (id: number, error: string) =>
  setStatus(id, "failed", { error });

export async function incrementAttempts(id: number): Promise<number> {
  const db = await getDb();
  const existing = (await db.get(STORE, id)) as QueuedOperation | undefined;
  if (!existing) return 0;
  const attempts = existing.attempts + 1;
  await db.put(STORE, { ...existing, attempts });
  return attempts;
}

export async function counts(): Promise<Record<QueuedStatus, number>> {
  const all = await listAll();
  const result: Record<QueuedStatus, number> = {
    pending: 0,
    applied: 0,
    conflict: 0,
    failed: 0,
  };
  for (const op of all) result[op.status] += 1;
  return result;
}
