export interface Accessory {
  id: string;
  name: string;
  category: string | null;
  subcategory: string | null;
  compatibleSubCategories: string[] | null;
  sizeSpecifications: Record<string, unknown> | null;
  quantityTotal: number;
  readonly quantityInUse: number;
  quantityAvailable: number;
  isLowStock: boolean;
  minimumStockAlert: number;
  reorderQuantity: number | null;
  unitCost: string | null;
  currency: string;
  supplierId: string | null;
  supplierSku: string | null;
  supplierUrl: string | null;
  notes: string | null;
}

export interface AccessoryCreate {
  name: string;
  category?: string | null;
  quantityTotal?: number;
  minimumStockAlert?: number;
  reorderQuantity?: number | null;
  unitCost?: string | null;
  currency?: string;
  supplierId?: string | null;
  notes?: string | null;
}

export type AccessoryUpdate = Partial<AccessoryCreate>;

export interface LowStockEntry {
  id: string;
  name: string;
  quantityAvailable: number;
  minimumStockAlert: number;
  reorderQuantity: number | null;
}

export interface ItemAccessoryAssignment {
  id: string;
  collectionItemId: string;
  accessoryId: string;
  quantityUsed: number;
  assignedAt: string | null;
  notes: string | null;
}
