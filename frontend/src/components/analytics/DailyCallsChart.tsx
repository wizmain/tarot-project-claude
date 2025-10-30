"use client";

/**
 * Daily Calls Chart - 일별 호출 수 추세 차트
 *
 * 이 컴포넌트의 목적:
 * - 일별 LLM 호출 수를 Bar Chart로 시각화
 * - 일별 트래픽 패턴 확인
 * - 툴팁으로 상세 정보 표시
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

interface DailyTrendData {
  date: string;
  total_cost: number;
  total_calls: number;
  avg_latency: number;
  by_model: { [key: string]: { calls: number; cost: number } };
}

interface Props {
  data: DailyTrendData[];
}

export default function DailyCallsChart({ data }: Props) {
  // 차트 데이터 변환
  const chartData = data.map((item) => ({
    date: format(new Date(item.date), "MM/dd", { locale: ko }),
    fullDate: item.date,
    calls: item.total_calls,
  }));

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="text-sm font-semibold text-gray-900 mb-2">
            {format(new Date(payload[0].payload.fullDate), "yyyy년 MM월 dd일", {
              locale: ko,
            })}
          </p>
          <p className="text-sm text-gray-700">
            호출 수: <span className="font-semibold">{payload[0].value.toLocaleString()}회</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">일별 호출 수 추세</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            tickFormatter={(value) => value.toLocaleString()}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar
            dataKey="calls"
            name="호출 수"
            fill="#10b981"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
