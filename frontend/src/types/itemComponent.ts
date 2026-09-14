/**
 * Types for item components.
 *
 * Components track individual parts of a collection item (box, manual, cartridge, etc.)
 * and their presence/condition status.
 */

/**
 * Component type - categorizes the component's role
 */
export type ComponentType =
  | "required"
  | "optional"
  | "accessory"
  | "packaging"
  | "documentation"
  | "media"
  | "hardware"
  | "other";

/**
 * ItemComponent - a component tracked for a collection item
 */
export interface ItemComponent {
  readonly id: string;
  readonly collectionItemId: string;
  readonly standardComponentId: string | null;
  readonly componentName: string;
  readonly componentType: ComponentType | null;
  readonly isPresent: boolean;
  readonly condition: string | null;
  readonly conditionNotes: string | null;
  readonly variantDescription: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
}

/**
 * ComponentTemplateEntry - a template entry from standard components
 *
 * Represents a standard component that should be checked off for items
 * in a given sub-category.
 */
export interface ComponentTemplateEntry {
  readonly standardComponentId: string;
  readonly componentName: string;
  readonly componentType: ComponentType | null;
  readonly description: string | null;
  readonly sortOrder: number;
  readonly isPresent: boolean;
  readonly recordedComponentId: string | null;
}

/**
 * CompletenessResult - result of a completeness check
 *
 * Returned after operations that may affect item completeness.
 */
export interface CompletenessResult {
  readonly isComplete: boolean;
  readonly requiredCount: number;
  readonly presentCount: number;
  readonly missingNames: string[];
}

/**
 * ItemComponentCreate - data for creating a new component
 */
export interface ItemComponentCreate {
  readonly standardComponentId?: string | null;
  readonly componentName: string;
  readonly componentType?: ComponentType | null;
  readonly isPresent?: boolean;
  readonly condition?: string | null;
  readonly conditionNotes?: string | null;
  readonly variantDescription?: string | null;
}

/**
 * ItemComponentUpdate - data for partially updating a component
 */
export interface ItemComponentUpdate {
  readonly standardComponentId?: string | null;
  readonly componentName?: string;
  readonly componentType?: ComponentType | null;
  readonly isPresent?: boolean;
  readonly condition?: string | null;
  readonly conditionNotes?: string | null;
  readonly variantDescription?: string | null;
}
