export type QueuedStatus = "pending" | "applied" | "conflict" | "failed";

export interface QueuedOperation {
  /** Autoincrement id defining FIFO order. */
  id: number;
  entityType: string;
  entityId: string | null;
  method: "POST" | "PUT" | "DELETE";
  endpoint: string;
  body: unknown;
  /** Server updatedAt captured at enqueue time, for conflict detection. */
  entityUpdatedAt: string | null;
  status: QueuedStatus;
  attempts: number;
  error: string | null;
  createdAt: number;
}

export type NewQueuedOperation = Omit<
  QueuedOperation,
  "id" | "status" | "attempts" | "error" | "createdAt"
>;
