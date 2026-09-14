export type ChartMarker = "circle" | "square" | "triangle" | "diamond";

export interface ChartPoint {
  label: string;
  value: number;
}

export interface ChartSeries {
  key: string;
  label: string;
  marker: ChartMarker;
  dashArray?: string;
  points: ChartPoint[];
}
