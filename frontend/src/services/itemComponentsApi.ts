/**
 * API client for item components.
 *
 * Provides methods for managing components tracked for collection items.
 */

import { fetchApi, toSnakeCase } from "./api";
import type {
  ItemComponent,
  ItemComponentCreate,
  ItemComponentUpdate,
  ComponentTemplateEntry,
  CompletenessResult,
} from "../types/itemComponent";

export const itemComponentsApi = {
  /**
   * Get the component template for a collection item's sub-category.
   * Returns standard components defined for the sub-category with their recorded presence.
   */
  template: (collectionItemId: string): Promise<ComponentTemplateEntry[]> =>
    fetchApi<ComponentTemplateEntry[]>(
      `/collection-items/${collectionItemId}/components/template`
    ),

  /**
   * List all components for a collection item.
   */
  list: (collectionItemId: string): Promise<ItemComponent[]> =>
    fetchApi<ItemComponent[]>(
      `/collection-items/${collectionItemId}/components`
    ),

  /**
   * Create or update a component for a collection item.
   * If a component with the same standard_component_id exists, it will be updated.
   * Returns the component and the completeness result.
   */
  upsert: (
    collectionItemId: string,
    data: ItemComponentCreate
  ): Promise<{ component: ItemComponent; completeness: CompletenessResult }> =>
    fetchApi<{
      component: ItemComponent;
      completeness: CompletenessResult;
    }>(`/collection-items/${collectionItemId}/components`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  /**
   * Partially update a component.
   * Returns the component and the completeness result.
   */
  update: (
    componentId: string,
    data: ItemComponentUpdate
  ): Promise<{ component: ItemComponent; completeness: CompletenessResult }> =>
    fetchApi<{
      component: ItemComponent;
      completeness: CompletenessResult;
    }>(`/item-components/${componentId}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  /**
   * Delete a component.
   * Returns the completeness result for the parent collection item.
   */
  remove: (componentId: string): Promise<CompletenessResult> =>
    fetchApi<CompletenessResult>(`/item-components/${componentId}`, {
      method: "DELETE",
    }),
};
