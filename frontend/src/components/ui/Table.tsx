import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";

export type SortDirection = "ascending" | "descending" | "none";

export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface TableProps<T> {
  caption: string;
  columns: TableColumn<T>[];
  rows: T[];
  /** Optional row key extractor. Defaults to row.id or index. */
  getRowKey?: (row: T, index: number) => string;
  onSort?: (columnKey: string, direction: SortDirection) => void;
  className?: string;
}

export function Table<T>({
  caption,
  columns,
  rows,
  getRowKey,
  onSort,
  className = "",
}: TableProps<T>) {
  const { t } = useTranslation();
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("none");

  const handleSort = useCallback(
    (columnKey: string) => {
      let newDirection: SortDirection = "ascending";

      if (sortColumn === columnKey) {
        if (sortDirection === "ascending") {
          newDirection = "descending";
        } else if (sortDirection === "descending") {
          newDirection = "none";
        }
      }

      setSortColumn(newDirection === "none" ? null : columnKey);
      setSortDirection(newDirection);
      onSort?.(columnKey, newDirection);
    },
    [sortColumn, sortDirection, onSort]
  );

  const getAriaSort = (columnKey: string): "ascending" | "descending" | "none" | undefined => {
    if (sortColumn !== columnKey) {
      return "none";
    }
    return sortDirection;
  };

  const getSortLabel = (columnKey: string, header: string): string => {
    const currentSort = sortColumn === columnKey ? sortDirection : "none";
    if (currentSort === "ascending") {
      return t("a11y.sortAscending", { column: header });
    }
    if (currentSort === "descending") {
      return t("a11y.sortDescending", { column: header });
    }
    return t("a11y.sortNone", { column: header });
  };

  const defaultGetRowKey = (row: T, index: number): string => {
    const rowWithId = row as { id?: unknown };
    if (rowWithId.id !== undefined) {
      return String(rowWithId.id);
    }
    return `row-${index}`;
  };

  const resolveRowKey = getRowKey ?? defaultGetRowKey;

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => {
              const columnKey = String(column.key);
              const isSortable = column.sortable ?? false;

              return (
                <th
                  key={columnKey}
                  scope="col"
                  style={column.width ? { width: column.width } : undefined}
                  aria-sort={isSortable ? getAriaSort(columnKey) : undefined}
                  className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700 ${
                    isSortable ? "cursor-pointer select-none hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500" : ""
                  }`}
                  {...(isSortable && {
                    tabIndex: 0,
                    onClick: () => handleSort(columnKey),
                    onKeyDown: (e: React.KeyboardEvent) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleSort(columnKey);
                      }
                    },
                    "aria-label": getSortLabel(columnKey, column.header),
                  })}
                >
                  <div className="flex items-center gap-2">
                    <span>{column.header}</span>
                    {isSortable && (
                      <span className="text-gray-400" aria-hidden="true">
                        {sortColumn === columnKey && sortDirection === "ascending" && "↑"}
                        {sortColumn === columnKey && sortDirection === "descending" && "↓"}
                        {sortColumn !== columnKey && "↕"}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-500">
                {t("common.noResults")}
              </td>
            </tr>
          ) : (
            rows.map((row, rowIndex) => {
              const rowKey = resolveRowKey(row, rowIndex);
              return (
                <tr key={rowKey} className="hover:bg-gray-50">
                  {columns.map((column) => {
                    const columnKey = String(column.key);
                    return (
                      <td
                        key={`${rowKey}-${columnKey}`}
                        className="whitespace-nowrap px-4 py-3 text-sm text-gray-900"
                      >
                        {column.accessor(row)}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
