/**
 * Grouped item list component.
 *
 * Displays collection items grouped by main/sub category with item counts.
 */

import { useTranslation } from "react-i18next";
import type { CollectionItemGroup } from "../../types/collection";

interface GroupedItemListProps {
  groups: CollectionItemGroup[];
  onEditItem?: (itemId: string) => void;
}

export function GroupedItemList({ groups, onEditItem }: GroupedItemListProps) {
  const { t } = useTranslation();

  if (groups.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("collections.grouped.empty")}
      </p>
    );
  }

  return (
    <section
      aria-labelledby="grouped-items-heading"
      className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
    >
      <h3
        id="grouped-items-heading"
        className="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
      >
        {t("collections.grouped.title")}
      </h3>

      <ul className="space-y-2" role="list">
        {groups.map((group, index) => (
          <li
            key={`${group.mainCategoryId ?? "none"}-${group.subCategoryId ?? "none"}-${index}`}
            className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2 dark:bg-gray-700"
          >
            <div className="flex flex-col">
              <span className="font-medium text-gray-900 dark:text-white">
                {group.mainCategoryName ?? t("collections.grouped.uncategorized")}
              </span>
              {group.subCategoryName && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {group.subCategoryName}
                </span>
              )}
            </div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {t("collections.grouped.itemCount", { count: group.itemCount })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
