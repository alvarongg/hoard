import { useTranslation } from "react-i18next";

import { usePending } from "../hooks/useCollectorWorkflow";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

const ENTITY_TYPES = [
  "supplier",
  "catalog",
  "catalog_item",
  "collection_item",
] as const;

export function PendingPage() {
  const { t } = useTranslation();
  const { data: pendings = [], isLoading, isError, resolve } = usePending();

  if (isLoading) return <LoadingSpinner />;
  if (isError) return <ErrorMessage message={t("common.error")} />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("pending.title")}</h1>
      <p className="text-sm text-gray-600">{t("pending.description")}</p>

      {pendings.length === 0 ? (
        <EmptyState title={t("pending.empty")} />
      ) : (
        ENTITY_TYPES.map((type) => {
          const group = pendings.filter((p) => p.entityType === type);
          if (group.length === 0) return null;
          return (
            <Card key={type} title={t(`pending.entity.${type}`)}>
              <ul className="flex flex-col gap-3">
                {group.map((p) => (
                  <li
                    key={p.id}
                    className="flex flex-col gap-2 border-b border-gray-200 pb-2"
                  >
                    <span className="text-sm text-gray-600">
                      {t("pending.missing")}: {p.missingFields.join(", ")}
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {p.missingFields.map((field) => (
                        <Button
                          key={field}
                          type="button"
                          variant="secondary"
                          onClick={() =>
                            resolve.mutate({
                              id: p.id,
                              completedFields: [field],
                            })
                          }
                        >
                          {t("pending.markDone", { field })}
                        </Button>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          );
        })
      )}
    </div>
  );
}
