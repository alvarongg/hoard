import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  useCollectionCatalogMutations,
  useCollectionCatalogs,
} from "../../hooks/useCollectorWorkflow";
import { useCatalogs } from "../../hooks/useCatalogs";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Select } from "../ui/Select";
import { CatalogQuickAdd } from "./CatalogQuickAdd";

interface CollectionCatalogsSectionProps {
  collectionId: string;
}

export function CollectionCatalogsSection({
  collectionId,
}: CollectionCatalogsSectionProps) {
  const { t } = useTranslation();
  const { data: linked = [] } = useCollectionCatalogs(collectionId);
  const { data: allCatalogs = [] } = useCatalogs();
  const { associate, dissociate, quickAdd } =
    useCollectionCatalogMutations(collectionId);
  const [selected, setSelected] = useState("");
  const [showQuickAdd, setShowQuickAdd] = useState(false);

  const linkedIds = new Set(linked.map((c) => c.id));
  const available = allCatalogs.filter((c) => !linkedIds.has(c.id));

  return (
    <Card>
      <h2 className="mb-2 text-lg font-semibold text-gray-900">
        {t("collector.collectionCatalogs.title")}
      </h2>
      {linked.length === 0 ? (
        <p className="text-sm text-gray-500">
          {t("collector.collectionCatalogs.empty")}
        </p>
      ) : (
        <ul className="mb-3 flex flex-col gap-1">
          {linked.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between text-sm"
            >
              <span>{c.name}</span>
              <Button
                type="button"
                variant="secondary"
                onClick={() => dissociate.mutate(c.id)}
              >
                {t("collector.collectionCatalogs.remove")}
              </Button>
            </li>
          ))}
        </ul>
      )}

      {showQuickAdd ? (
        <CatalogQuickAdd
          isLoading={quickAdd.isPending}
          onCreate={(name, tematica) =>
            quickAdd.mutate(
              { name, tematica },
              { onSuccess: () => setShowQuickAdd(false) },
            )
          }
          onCancel={() => setShowQuickAdd(false)}
        />
      ) : (
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Select
              label={t("collector.collectionCatalogs.associate")}
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              options={[
                { value: "", label: t("collector.collectionCatalogs.choose") },
                ...available.map((c) => ({ value: c.id, label: c.name })),
              ]}
            />
          </div>
          <Button
            type="button"
            disabled={!selected}
            onClick={() =>
              associate.mutate(
                { catalogId: selected },
                { onSuccess: () => setSelected("") },
              )
            }
          >
            {t("collector.collectionCatalogs.add")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setShowQuickAdd(true)}
          >
            {t("collector.collectionCatalogs.new")}
          </Button>
        </div>
      )}
    </Card>
  );
}
