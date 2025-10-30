"use client";

/**
 * Daily Cost Chart - 일별 비용 추세 차트
 *
 * 이 컴포넌트의 목적:
 * - 일별 LLM 사용 비용을 Line Chart로 시각화
 * - 모델별 비용을 색상으로 구분
 * - 툴팁으로 상세 정보 표시
 *
 * 사용 라이브러리:
 * - Recharts: 반응형 차트 라이브러리
 * - date-fns: 날짜 포맷팅
 */

import {
  LineChart,
  Line,
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

export default function DailyCostChart({ data }: Props) {
  // 차트 데이터 변환: 날짜별로 total_cost만 추출
  const chartData = data.map((item) => ({
    date: format(new Date(item.date), "MM/dd", { locale: ko }),
    fullDate: item.date,
    cost: parseFloat(item.total_cost.toFixed(4)),
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
            비용: <span className="font-semibold">${payload[0].value.toFixed(4)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">일별 비용 추세</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            tickFormatter={(value) => `$${value.toFixed(4)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="cost"
            name="비용"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ fill: "#6366f1", r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
