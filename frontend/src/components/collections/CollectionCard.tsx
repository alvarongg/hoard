import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { Collection, CollectionType } from "../../types/collection";

interface CollectionCardProps {
  collection: Collection;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const TYPE_KEYS: Record<CollectionType, string> = {
  single_category: "collections.singleCategory",
  multi_category: "collections.multiCategory",
  mixed: "collections.mixed",
};

export function CollectionCard({
  collection,
  onEdit,
  onDelete,
}: CollectionCardProps) {
  const { t } = useTranslation();
  const headingId = `collection-${collection.id}`;

  return (
    <article
      aria-labelledby={headingId}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      <h3 id={headingId} className="text-lg font-semibold text-gray-900">
        <Link
          to={`/collections/${collection.id}`}
          className="text-blue-700 hover:underline"
        >
          {collection.name}
        </Link>
      </h3>
      <p className="mt-1 text-sm text-gray-500">
        {t(TYPE_KEYS[collection.collectionType])}
      </p>
      {collection.description && (
        <p className="mt-1 text-sm text-gray-600">{collection.description}</p>
      )}
      <div className="mt-3 flex gap-2">
        <Link
          to={`/collections/${collection.id}`}
          className="rounded-md bg-gray-200 px-3 py-1 text-sm text-gray-800 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
        >
          {t("common.view")}
        </Link>
        <button
          onClick={() => onEdit(collection.id)}
          aria-label={t("collections.editLabel", { name: collection.name })}
          className="rounded-md bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {t("common.edit")}
        </button>
        <button
          onClick={() => onDelete(collection.id)}
          aria-label={t("collections.deleteLabel", { name: collection.name })}
          className="rounded-md bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          {t("common.delete")}
        </button>
      </div>
    </article>
  );
}
