"use client";

/**
 * Latency Histogram - 응답 시간 분포 히스토그램
 *
 * 이 컴포넌트의 목적:
 * - LLM 응답 시간 분포를 히스토그램으로 시각화
 * - 성능 패턴 및 이상치 확인
 * - 구간별 호출 수 표시
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface RecentLogEntry {
  id: string;
  reading_id: string;
  created_at: string;
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  latency_seconds: number;
  purpose: string;
  reading_question?: string;
}

interface Props {
  data: RecentLogEntry[];
}

// 응답 시간을 구간별로 그룹화
function groupByLatency(logs: RecentLogEntry[]) {
  const buckets = [
    { range: "0-5s", min: 0, max: 5, count: 0 },
    { range: "5-10s", min: 5, max: 10, count: 0 },
    { range: "10-20s", min: 10, max: 20, count: 0 },
    { range: "20-30s", min: 20, max: 30, count: 0 },
    { range: "30s+", min: 30, max: Infinity, count: 0 },
  ];

  logs.forEach((log) => {
    const latency = log.latency_seconds;
    for (const bucket of buckets) {
      if (latency >= bucket.min && latency < bucket.max) {
        bucket.count++;
        break;
      }
    }
  });

  return buckets;
}

export default function LatencyHistogram({ data }: Props) {
  const chartData = groupByLatency(data);

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="text-sm font-semibold text-gray-900 mb-2">
            응답 시간: {payload[0].payload.range}
          </p>
          <p className="text-sm text-gray-700">
            호출 수: <span className="font-semibold">{payload[0].value.toLocaleString()}회</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            전체 대비: {((payload[0].value / data.length) * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        응답 시간 분포
      </h2>
      <p className="text-sm text-gray-600 mb-4">
        총 {data.length.toLocaleString()}건의 호출 기록
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="range"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            tickFormatter={(value) => value.toLocaleString()}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="count"
            name="호출 수"
            fill="#8b5cf6"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
