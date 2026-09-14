import { API_BASE_URL } from "../services/api";
import {
  listByStatus,
  markApplied,
  markConflict,
  markFailed,
  incrementAttempts,
} from "./queue";
import type { QueuedOperation } from "./types";

const MAX_ATTEMPTS = 5;

let draining = false;

interface DrainResult {
  applied: number;
  conflicts: number;
  failed: number;
  remaining: number;
}

/**
 * Process pending operations strictly in FIFO (id) order.
 *
 * - Before PUT/DELETE, GET the entity; if the server's updatedAt is newer
 *   than the one captured at enqueue time, mark conflict and skip.
 * - A 4xx other than 409 marks the op failed (no retry).
 * - A network error increments attempts (max 5) and stops the drain,
 *   leaving the rest pending.
 * A single-flight guard prevents two concurrent drains from double-sending.
 */
export async function drainQueue(): Promise<DrainResult> {
  const result: DrainResult = {
    applied: 0,
    conflicts: 0,
    failed: 0,
    remaining: 0,
  };
  if (draining) return result;
  draining = true;
  try {
    const pending = await listByStatus("pending");
    for (const op of pending) {
      try {
        if (await _hasConflict(op)) {
          await markConflict(op.id);
          result.conflicts += 1;
          continue;
        }
        const response = await fetch(`${API_BASE_URL}${op.endpoint}`, {
          method: op.method,
          headers:
            op.method === "DELETE"
              ? undefined
              : { "Content-Type": "application/json" },
          body: op.method === "DELETE" ? undefined : JSON.stringify(op.body),
        });
        if (response.ok) {
          await markApplied(op.id);
          result.applied += 1;
        } else if (response.status === 409) {
          await markConflict(op.id);
          result.conflicts += 1;
        } else if (response.status >= 400 && response.status < 500) {
          await markFailed(op.id, `HTTP ${response.status}`);
          result.failed += 1;
        } else {
          // 5xx: treat like a transient error.
          throw new Error(`HTTP ${response.status}`);
        }
      } catch {
        const attempts = await incrementAttempts(op.id);
        if (attempts >= MAX_ATTEMPTS) {
          await markFailed(op.id, "max attempts reached");
          result.failed += 1;
        } else {
          // Network error: stop the drain, leave the rest pending.
          result.remaining =
            pending.length - (result.applied + result.conflicts + result.failed);
          return result;
        }
      }
    }
    return result;
  } finally {
    draining = false;
  }
}

async function _hasConflict(op: QueuedOperation): Promise<boolean> {
  if (op.method === "POST" || !op.entityId || !op.entityUpdatedAt) {
    return false;
  }
  try {
    const response = await fetch(`${API_BASE_URL}${op.endpoint}`, {
      method: "GET",
    });
    if (!response.ok) return false;
    const data: unknown = await response.json();
    const serverUpdated =
      typeof data === "object" && data !== null && "updatedAt" in data
        ? String((data as { updatedAt: unknown }).updatedAt)
        : null;
    if (serverUpdated === null) return false;
    return new Date(serverUpdated) > new Date(op.entityUpdatedAt);
  } catch {
    return false;
  }
}
