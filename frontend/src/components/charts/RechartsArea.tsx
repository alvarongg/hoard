import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSeries } from "../../types/chart";

interface RechartsAreaProps {
  series: ChartSeries[];
}

/** Area chart renderer. Default export for React.lazy code-splitting. */
export default function RechartsArea({ series }: RechartsAreaProps) {
  const first = series[0];
  if (!first) return null;
  const data = first.points.map((p) => ({ label: p.label, value: p.value }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis />
        <Tooltip />
        <Area
          dataKey="value"
          stroke="#2563eb"
          fill="#93c5fd"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
