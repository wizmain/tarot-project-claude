"use client";

/**
 * Model Breakdown Chart - 모델별 사용 비율 차트
 *
 * 이 컴포넌트의 목적:
 * - 모델별 비용/호출 수를 Pie Chart로 시각화
 * - 각 모델의 사용 비율 확인
 * - 색상으로 모델 구분
 */

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface ModelStats {
  model: string;
  provider: string;
  calls: number;
  total_cost: number;
  avg_latency: number;
}

interface Props {
  data: ModelStats[];
  metric: "cost" | "calls";
}

// 모델별 색상 팔레트
const COLORS = [
  "#6366f1", // indigo
  "#10b981", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#06b6d4", // cyan
  "#ec4899", // pink
];

export default function ModelBreakdownChart({ data, metric }: Props) {
  // 차트 데이터 변환
  const chartData = data.map((item, index) => ({
    name: `${item.provider}/${item.model}`,
    value: metric === "cost" ? item.total_cost : item.calls,
    color: COLORS[index % COLORS.length],
    fullData: item,
  }));

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload.fullData;
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="text-sm font-semibold text-gray-900 mb-2">
            {data.provider} - {data.model}
          </p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-700">
              비용: <span className="font-semibold">${data.total_cost.toFixed(4)}</span>
            </p>
            <p className="text-gray-700">
              호출 수: <span className="font-semibold">{data.calls.toLocaleString()}회</span>
            </p>
            <p className="text-gray-700">
              평균 응답: <span className="font-semibold">{data.avg_latency.toFixed(2)}초</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // 커스텀 레이블
  const renderLabel = (entry: any) => {
    const percent = ((entry.value / chartData.reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1);
    return `${percent}%`;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        모델별 {metric === "cost" ? "비용" : "호출 수"} 분포
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderLabel}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value, entry: any) => {
              const item = chartData.find((d) => d.name === value);
              if (!item) return value;
              const displayValue = metric === "cost"
                ? `$${item.value.toFixed(4)}`
                : `${item.value.toLocaleString()}회`;
              return `${value}: ${displayValue}`;
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
