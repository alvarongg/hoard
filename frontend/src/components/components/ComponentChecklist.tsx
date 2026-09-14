/**
 * ComponentChecklist - Checklist of components for a collection item.
 *
 * Fetches the component template and displays each component with a checkbox.
 * Announces completeness changes via useAnnouncement.
 */

import { useTranslation } from "react-i18next";
import { useComponentTemplate, useItemComponentMutations, type OnCompletenessChange } from "../../hooks/useItemComponents";
import { ComponentRow } from "./ComponentRow";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { useAnnouncement } from "../../hooks/useAnnouncement";

interface ComponentChecklistProps {
  /** The collection item ID */
  collectionItemId: string;
  /** Callback when completeness changes */
  onCompletenessChange?: OnCompletenessChange;
}

export function ComponentChecklist({
  collectionItemId,
  onCompletenessChange,
}: ComponentChecklistProps) {
  const { t } = useTranslation();
  const announce = useAnnouncement();
  const { data: template, isLoading, error, refetch } = useComponentTemplate(collectionItemId);
  const { upsert } = useItemComponentMutations(collectionItemId);

  function handleCompletenessChange(result: Parameters<OnCompletenessChange>[0]) {
    // Announce the change
    if (result.isComplete) {
      announce(t("components.completenessAnnouncement.complete"), "polite");
    } else {
      announce(
        t("components.completenessAnnouncement.incomplete", {
          missing: result.missingNames.join(", "),
        }),
        "polite"
      );
    }

    // Notify parent
    onCompletenessChange?.(result);
  }

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <ErrorMessage
        message={t("errors.loadFailed")}
        onRetry={() => refetch()}
      />
    );
  }

  if (!template || template.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        {t("components.template.empty")}
      </p>
    );
  }

  // Separate required and optional components
  const requiredComponents = template.filter(
    (e) => e.componentType === "required"
  );
  const optionalComponents = template.filter(
    (e) => e.componentType !== "required"
  );

  return (
    <section aria-labelledby="component-checklist-heading">
      <h3 id="component-checklist-heading" className="sr-only">
        {t("components.title")}
      </h3>

      {requiredComponents.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {t("components.requiredComponents")}
          </h4>
          <div className="space-y-1">
            {requiredComponents.map((entry) => (
              <ComponentRow
                key={entry.standardComponentId}
                entry={entry}
                collectionItemId={collectionItemId}
                onCompletenessChange={handleCompletenessChange}
              />
            ))}
          </div>
        </div>
      )}

      {optionalComponents.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {t("components.optionalComponents")}
          </h4>
          <div className="space-y-1">
            {optionalComponents.map((entry) => (
              <ComponentRow
                key={entry.standardComponentId}
                entry={entry}
                collectionItemId={collectionItemId}
                onCompletenessChange={handleCompletenessChange}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
