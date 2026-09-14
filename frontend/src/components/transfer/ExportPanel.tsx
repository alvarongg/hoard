import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";
import { ErrorMessage } from "../ui/ErrorMessage";
import { useExport } from "../../hooks/useTransfer";
import type { ExportFormat } from "../../types/transfer";

export function ExportPanel() {
  const { t } = useTranslation();
  const exporter = useExport();
  const [entity, setEntity] = useState<"collection" | "catalog" | "wishlist">(
    "wishlist",
  );
  const [id, setId] = useState("");
  const [format, setFormat] = useState<ExportFormat>("json");

  function handleExport() {
    if (entity === "wishlist") {
      exporter.mutate({ kind: "wishlist" });
    } else if (entity === "collection") {
      exporter.mutate({ kind: "collection", id });
    } else {
      exporter.mutate({ kind: "catalog", id, format });
    }
  }

  return (
    <div className="space-y-3">
      <Select
        label={t("export.entity")}
        value={entity}
        onChange={(e) =>
          setEntity(e.target.value as "collection" | "catalog" | "wishlist")
        }
        options={[
          { value: "wishlist", label: t("export.entityWishlist") },
          { value: "collection", label: t("export.entityCollection") },
          { value: "catalog", label: t("export.entityCatalog") },
        ]}
      />

      {entity !== "wishlist" && (
        <Input
          label="ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
      )}

      {entity === "catalog" && (
        <Select
          label={t("export.format")}
          value={format}
          onChange={(e) => setFormat(e.target.value as ExportFormat)}
          options={[
            { value: "json", label: "JSON" },
            { value: "csv", label: "CSV" },
          ]}
        />
      )}

      {exporter.isError && (
        <ErrorMessage message={t("errors.export.failed")} />
      )}

      <Button onClick={handleExport} disabled={exporter.isPending}>
        {exporter.isPending ? t("export.inProgress") : t("export.download")}
      </Button>
    </div>
  );
}
