import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSeries } from "../../types/chart";

interface RechartsBarsProps {
  series: ChartSeries[];
}

/** Bar chart renderer. Default export for React.lazy code-splitting. */
export default function RechartsBars({ series }: RechartsBarsProps) {
  const first = series[0];
  if (!first) return null;
  const data = first.points.map((p) => ({ label: p.label, value: p.value }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="value" fill="#2563eb" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
