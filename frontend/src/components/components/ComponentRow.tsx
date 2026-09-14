/**
 * ComponentRow - A single row in the component checklist.
 *
 * Displays a component with its presence checkbox, condition, and notes.
 * Announces changes via the onCompletenessChange callback.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ComponentTemplateEntry, CompletenessResult } from "../../types/itemComponent";
import { useItemComponentMutations, type OnCompletenessChange } from "../../hooks/useItemComponents";
import { useAnnouncement } from "../../hooks/useAnnouncement";

interface ComponentRowProps {
  /** The template entry for this component */
  entry: ComponentTemplateEntry;
  /** The collection item ID */
  collectionItemId: string;
  /** Callback when completeness changes */
  onCompletenessChange: OnCompletenessChange;
}

export function ComponentRow({
  entry,
  collectionItemId,
  onCompletenessChange,
}: ComponentRowProps) {
  const { t } = useTranslation();
  const announce = useAnnouncement();
  const { upsert, remove } = useItemComponentMutations(collectionItemId);

  const [isExpanded, setIsExpanded] = useState(false);
  const [condition, setCondition] = useState("");
  const [conditionNotes, setConditionNotes] = useState("");

  async function handleToggle() {
    const newIsPresent = !entry.isPresent;

    if (newIsPresent) {
      // Mark as present - upsert
      const result = await upsert.mutateAsync({
        standardComponentId: entry.standardComponentId,
        componentName: entry.componentName,
        componentType: entry.componentType,
        isPresent: true,
        condition: condition || undefined,
        conditionNotes: conditionNotes || undefined,
      });

      onCompletenessChange(result.completeness);
      announce(
        t("components.present", { name: entry.componentName }),
        "polite"
      );
    } else if (entry.recordedComponentId) {
      // Mark as not present - delete the recorded component
      const completenessResult = await remove.mutateAsync(entry.recordedComponentId);
      onCompletenessChange(completenessResult);
      announce(
        t("components.absent", { name: entry.componentName }),
        "polite"
      );
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleToggle();
    }
  }

  return (
    <div className="flex items-start gap-3 py-2">
      <div className="flex items-center">
        <input
          type="checkbox"
          id={`component-${entry.standardComponentId}`}
          checked={entry.isPresent}
          onChange={handleToggle}
          onKeyDown={handleKeyDown}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          aria-label={t("components.toggleComponent", {
            name: entry.componentName,
            status: entry.isPresent ? "present" : "absent",
          })}
        />
      </div>

      <div className="flex-1 min-w-0">
        <label
          htmlFor={`component-${entry.standardComponentId}`}
          className="block text-sm font-medium text-gray-900 cursor-pointer"
        >
          {entry.componentName}
          {entry.componentType === "required" && (
            <span className="ml-2 text-xs text-gray-500">
              ({t("components.required")})
            </span>
          )}
        </label>

        {entry.description && (
          <p className="text-xs text-gray-500 mt-0.5">{entry.description}</p>
        )}

        {entry.isPresent && (
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-blue-600 hover:text-blue-800 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-expanded={isExpanded}
          >
            {isExpanded
              ? t("components.hideDetails")
              : t("components.addDetails")}
          </button>
        )}

        {entry.isPresent && isExpanded && (
          <div className="mt-2 space-y-2">
            <div>
              <label
                htmlFor={`condition-${entry.standardComponentId}`}
                className="block text-xs text-gray-600"
              >
                {t("components.condition")}
              </label>
              <input
                type="text"
                id={`condition-${entry.standardComponentId}`}
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
            <div>
              <label
                htmlFor={`notes-${entry.standardComponentId}`}
                className="block text-xs text-gray-600"
              >
                {t("components.conditionNotes")}
              </label>
              <textarea
                id={`notes-${entry.standardComponentId}`}
                value={conditionNotes}
                onChange={(e) => setConditionNotes(e.target.value)}
                rows={2}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
