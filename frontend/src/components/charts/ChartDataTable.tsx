import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import type { ChartSeries } from "../../types/chart";

interface ChartDataTableProps {
  caption: string;
  series: ChartSeries[];
}

interface Row {
  label: string;
  [seriesKey: string]: string;
}

/**
 * ChartDataTable - the accessible, text equivalent of a chart.
 * One row per point label, one column per series.
 */
export function ChartDataTable({ caption, series }: ChartDataTableProps) {
  const { t } = useTranslation();

  // Union of all point labels across series, preserving first-seen order.
  const labels: string[] = [];
  for (const s of series) {
    for (const p of s.points) {
      if (!labels.includes(p.label)) labels.push(p.label);
    }
  }

  const rows: Row[] = labels.map((label) => {
    const row: Row = { label };
    for (const s of series) {
      const point = s.points.find((p) => p.label === label);
      row[s.key] = point ? String(point.value) : "—";
    }
    return row;
  });

  const columns: TableColumn<Row>[] = [
    {
      key: "label",
      header: t("charts.category", "Category"),
      accessor: (r) => r.label,
    },
    ...series.map((s) => ({
      key: s.key,
      header: s.label,
      accessor: (r: Row) => r[s.key] ?? "—",
    })),
  ];

  return (
    <Table
      caption={caption}
      columns={columns}
      rows={rows}
      getRowKey={(r) => r.label}
    />
  );
}
