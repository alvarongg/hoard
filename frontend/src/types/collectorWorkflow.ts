export interface OwnershipEntry {
  collectionItemId: string;
  collectionId: string;
  collectionName: string;
  condition: string;
}

export interface Ownership {
  catalogItemId: string;
  owned: boolean;
  count: number;
  entries: OwnershipEntry[];
}

export interface SupplierQuickAdd {
  name: string;
  country?: string | null;
}

export interface CatalogQuickAdd {
  name: string;
  tematica: string;
  isPrimary?: boolean;
}

export interface Pending {
  id: string;
  entityType: "collection_item" | "catalog" | "catalog_item" | "supplier";
  entityId: string;
  missingFields: string[];
  status: string;
  createdAt: string;
  resolvedAt?: string | null;
}

export interface MaintenanceSchedule {
  id: string;
  collectionItemId: string;
  maintenanceType: string;
  dueDate: string;
  notes?: string | null;
  isDone: boolean;
  doneDate?: string | null;
  doneNotes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MaintenanceCreate {
  maintenanceType: string;
  dueDate: string;
  notes?: string | null;
}
