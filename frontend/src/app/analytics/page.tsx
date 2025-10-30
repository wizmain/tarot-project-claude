"use client";

/**
 * Analytics Dashboard - LLM 사용 기록 대시보드
 *
 * 이 페이지의 목적:
 * - LLM 사용 통계 시각화 (비용, 호출 수, 응답 시간)
 * - 일별 추세 차트 표시
 * - 최근 LLM 호출 기록 테이블
 *
 * 주요 기능:
 * - Summary Cards: 총 비용, 총 호출 수, 평균 응답 시간, 이전 기간 대비 변화율
 * - Daily Trend Chart: 일별 비용/호출 수 추세 (Recharts 사용)
 * - Recent Calls Table: 최근 LLM 호출 기록 (페이지네이션)
 *
 * Phase 1 구현 범위:
 * - 기본 레이아웃 및 데이터 fetching
 * - 3가지 API 엔드포인트 연동
 * - 로딩 및 에러 상태 처리
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/firebase";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import DailyCostChart from "@/components/analytics/DailyCostChart";
import DailyCallsChart from "@/components/analytics/DailyCallsChart";
import ModelBreakdownChart from "@/components/analytics/ModelBreakdownChart";
import LatencyHistogram from "@/components/analytics/LatencyHistogram";
import {
  exportSummaryToCSV,
  exportDailyTrendToCSV,
  exportRecentLogsToCSV,
} from "@/lib/utils/csvExport";

// API 응답 타입 정의
interface ModelStats {
  model: string;
  provider: string;
  calls: number;
  total_cost: number;
  avg_latency: number;
}

interface SummaryData {
  total_cost: number;
  total_calls: number;
  avg_latency_seconds: number;
  period_days: number;
  comparison: {
    cost_change_percent: number;
    calls_change_percent: number;
    latency_change_percent: number;
  };
  by_model: ModelStats[];
}

interface DailyTrendData {
  date: string;
  total_cost: number;
  total_calls: number;
  avg_latency: number;
  by_model: { [key: string]: { calls: number; cost: number } };
}

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyticsDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);

  // 데이터 상태
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [dailyTrend, setDailyTrend] = useState<DailyTrendData[]>([]);
  const [recentLogs, setRecentLogs] = useState<RecentLogEntry[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);

  // 필터 상태
  const [days, setDays] = useState(30);
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [selectedModel, setSelectedModel] = useState<string>("all");

  // Date Range Picker 상태
  const [useCustomRange, setUseCustomRange] = useState(false);
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date());

  // Auto-refresh 상태
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(60); // seconds

  // Budget Alerts 상태
  const [dailyBudget, setDailyBudget] = useState<number>(1.0); // USD
  const [monthlyBudget, setMonthlyBudget] = useState<number>(30.0); // USD
  const [showBudgetSettings, setShowBudgetSettings] = useState(false);

  // 인증 확인
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(async (user) => {
      if (user) {
        const token = await user.getIdToken();
        setAuthToken(token);
      } else {
        router.push("/login");
      }
    });

    return () => unsubscribe();
  }, [router]);

  // 데이터 fetch 함수 분리
  const fetchData = async () => {
    if (!authToken) return;
      setLoading(true);
      setError(null);

      try {
        const headers = {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        };

        // 1. Summary 데이터
        const summaryRes = await fetch(
          `${API_BASE_URL}/api/v1/analytics/llm-usage/summary?days=${days}`,
          { headers }
        );
        if (!summaryRes.ok) throw new Error("Failed to fetch summary data");
        const summary = await summaryRes.json();
        setSummaryData(summary);

        // 2. Daily trend 데이터
        const trendRes = await fetch(
          `${API_BASE_URL}/api/v1/analytics/llm-usage/daily-trend?days=${days}`,
          { headers }
        );
        if (!trendRes.ok) throw new Error("Failed to fetch trend data");
        const trend = await trendRes.json();
        setDailyTrend(trend.data);

        // 3. Recent logs 데이터
        const logsRes = await fetch(
          `${API_BASE_URL}/api/v1/analytics/llm-usage/recent?page=${page}&page_size=${pageSize}`,
          { headers }
        );
        if (!logsRes.ok) throw new Error("Failed to fetch recent logs");
        const logs = await logsRes.json();
        setRecentLogs(logs.logs);
        setTotalLogs(logs.total);
      } catch (err) {
        console.error("Error fetching analytics data:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
  };

  // 데이터 fetch
  useEffect(() => {
    fetchData();
  }, [authToken, days, page]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, authToken, days, page]);

  // 로딩 상태
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md">
          <div className="text-red-600 text-xl font-semibold mb-4">오류 발생</div>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 헤더 */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">LLM 사용 분석</h1>
            <p className="mt-2 text-gray-600">
              AI 모델 사용 통계 및 비용 분석 대시보드
            </p>
          </div>
          {/* Auto-refresh & Export 버튼들 */}
          <div className="flex flex-col gap-2">
            {/* Auto-refresh Controls */}
            <div className="flex items-center gap-2 justify-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">자동 새로고침</span>
              </label>
              {autoRefresh && (
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value={30}>30초</option>
                  <option value={60}>1분</option>
                  <option value={300}>5분</option>
                </select>
              )}
            </div>

            {/* Export 버튼들 */}
            <div className="flex gap-2">
            <button
              onClick={() => summaryData && exportSummaryToCSV(summaryData)}
              disabled={!summaryData}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              요약 Export
            </button>
            <button
              onClick={() => exportDailyTrendToCSV(dailyTrend)}
              disabled={dailyTrend.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              추세 Export
            </button>
            <button
              onClick={() => {
                const filteredLogs = recentLogs.filter((log) => {
                  if (
                    selectedProvider !== "all" &&
                    log.provider !== selectedProvider
                  )
                    return false;
                  if (selectedModel !== "all" && log.model !== selectedModel)
                    return false;
                  return true;
                });
                exportRecentLogsToCSV(filteredLogs);
              }}
              disabled={recentLogs.length === 0}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              로그 Export
            </button>
            </div>
          </div>
        </div>

        {/* 필터 섹션 */}
        <div className="mb-6 space-y-4">
          {/* 기간 선택 */}
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <span className="text-sm font-medium text-gray-700 self-center mr-2">
                기간:
              </span>
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => {
                    setDays(d);
                    setUseCustomRange(false);
                  }}
                  className={`px-4 py-2 rounded-md ${
                    days === d && !useCustomRange
                      ? "bg-indigo-600 text-white"
                      : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {d}일
                </button>
              ))}
              <button
                onClick={() => setUseCustomRange(!useCustomRange)}
                className={`px-4 py-2 rounded-md ${
                  useCustomRange
                    ? "bg-indigo-600 text-white"
                    : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                }`}
              >
                커스텀 기간
              </button>
            </div>

            {/* Date Range Picker */}
            {useCustomRange && (
              <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-md">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">
                    시작일:
                  </label>
                  <DatePicker
                    selected={startDate}
                    onChange={(date) => setStartDate(date)}
                    selectsStart
                    startDate={startDate}
                    endDate={endDate}
                    maxDate={new Date()}
                    dateFormat="yyyy-MM-dd"
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">
                    종료일:
                  </label>
                  <DatePicker
                    selected={endDate}
                    onChange={(date) => setEndDate(date)}
                    selectsEnd
                    startDate={startDate}
                    endDate={endDate}
                    minDate={startDate}
                    maxDate={new Date()}
                    dateFormat="yyyy-MM-dd"
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <button
                  onClick={() => {
                    if (startDate && endDate) {
                      const diffTime = Math.abs(
                        endDate.getTime() - startDate.getTime()
                      );
                      const diffDays = Math.ceil(
                        diffTime / (1000 * 60 * 60 * 24)
                      );
                      setDays(diffDays);
                    }
                  }}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                >
                  적용
                </button>
              </div>
            )}
          </div>

          {/* Provider/Model 필터 */}
          {summaryData && summaryData.by_model.length > 0 && (
            <div className="flex flex-wrap gap-4">
              {/* Provider 필터 */}
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">
                  Provider:
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">전체</option>
                  {Array.from(
                    new Set(summaryData.by_model.map((m) => m.provider))
                  ).map((provider) => (
                    <option key={provider} value={provider}>
                      {provider}
                    </option>
                  ))}
                </select>
              </div>

              {/* Model 필터 */}
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">
                  Model:
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">전체</option>
                  {summaryData.by_model
                    .filter(
                      (m) =>
                        selectedProvider === "all" ||
                        m.provider === selectedProvider
                    )
                    .map((model) => (
                      <option key={model.model} value={model.model}>
                        {model.model}
                      </option>
                    ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Budget Alerts */}
        {summaryData && (
          <div className="mb-6">
            {/* Budget Settings Toggle */}
            <button
              onClick={() => setShowBudgetSettings(!showBudgetSettings)}
              className="mb-4 text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              예산 설정 {showBudgetSettings ? "숨기기" : "보기"}
            </button>

            {/* Budget Settings */}
            {showBudgetSettings && (
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      일일 예산 (USD)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={dailyBudget}
                      onChange={(e) => setDailyBudget(parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      월간 예산 (USD)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={monthlyBudget}
                      onChange={(e) => setMonthlyBudget(parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Budget Alert Messages */}
            {days <= 1 && summaryData.total_cost > dailyBudget && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">
                      <span className="font-semibold">일일 예산 초과!</span> 현재 비용:{" "}
                      ${summaryData.total_cost.toFixed(4)} / 예산: ${dailyBudget.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {days === 30 && summaryData.total_cost > monthlyBudget && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">
                      <span className="font-semibold">월간 예산 초과!</span> 현재 비용:{" "}
                      ${summaryData.total_cost.toFixed(4)} / 예산: ${monthlyBudget.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Warning for approaching budget */}
            {days === 30 &&
              summaryData.total_cost > monthlyBudget * 0.8 &&
              summaryData.total_cost <= monthlyBudget && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-yellow-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-700">
                        <span className="font-semibold">예산 80% 도달</span> 현재 비용:{" "}
                        ${summaryData.total_cost.toFixed(4)} / 예산: ${monthlyBudget.toFixed(2)} (
                        {((summaryData.total_cost / monthlyBudget) * 100).toFixed(1)}%)
                      </p>
                    </div>
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Summary Cards */}
        {summaryData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* 총 비용 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-2">총 비용</div>
              <div className="text-3xl font-bold text-gray-900">
                ${summaryData.total_cost.toFixed(4)}
              </div>
              <div
                className={`text-sm mt-2 ${
                  summaryData.comparison.cost_change_percent > 0
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {summaryData.comparison.cost_change_percent > 0 ? "+" : ""}
                {summaryData.comparison.cost_change_percent.toFixed(1)}% (이전 기간 대비)
              </div>
            </div>

            {/* 총 호출 수 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-2">총 호출 수</div>
              <div className="text-3xl font-bold text-gray-900">
                {summaryData.total_calls.toLocaleString()}
              </div>
              <div
                className={`text-sm mt-2 ${
                  summaryData.comparison.calls_change_percent > 0
                    ? "text-blue-600"
                    : "text-gray-600"
                }`}
              >
                {summaryData.comparison.calls_change_percent > 0 ? "+" : ""}
                {summaryData.comparison.calls_change_percent.toFixed(1)}% (이전 기간 대비)
              </div>
            </div>

            {/* 평균 응답 시간 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-2">평균 응답 시간</div>
              <div className="text-3xl font-bold text-gray-900">
                {summaryData.avg_latency_seconds.toFixed(2)}초
              </div>
              <div
                className={`text-sm mt-2 ${
                  summaryData.comparison.latency_change_percent > 0
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {summaryData.comparison.latency_change_percent > 0 ? "+" : ""}
                {summaryData.comparison.latency_change_percent.toFixed(1)}% (이전 기간 대비)
              </div>
            </div>
          </div>
        )}

        {/* Daily Trend Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <DailyCostChart data={dailyTrend} />
          <DailyCallsChart data={dailyTrend} />
        </div>

        {/* Model Breakdown and Latency Charts */}
        {summaryData && summaryData.by_model.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <ModelBreakdownChart data={summaryData.by_model} metric="cost" />
            <LatencyHistogram data={recentLogs} />
          </div>
        )}

        {/* Recent Calls Table */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            최근 LLM 호출 기록
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    시간
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    모델
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    토큰
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    비용
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    응답시간
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    질문
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentLogs
                  .filter((log) => {
                    if (
                      selectedProvider !== "all" &&
                      log.provider !== selectedProvider
                    )
                      return false;
                    if (selectedModel !== "all" && log.model !== selectedModel)
                      return false;
                    return true;
                  })
                  .map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.created_at).toLocaleDateString("ko-KR")}
                      <br />
                      <span className="text-xs text-gray-500">
                        {new Date(log.created_at).toLocaleTimeString("ko-KR")}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {log.provider}
                      </div>
                      <div className="text-xs text-gray-500">{log.model}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.total_tokens.toLocaleString()}
                      <br />
                      <span className="text-xs text-gray-500">
                        ({log.prompt_tokens}/{log.completion_tokens})
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${log.estimated_cost.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.latency_seconds.toFixed(2)}초
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {log.reading_question || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalLogs > pageSize && (
            <div className="mt-4 flex justify-between items-center">
              <div className="text-sm text-gray-600">
                총 {totalLogs}개 중 {(page - 1) * pageSize + 1}-
                {Math.min(page * pageSize, totalLogs)}개 표시
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  이전
                </button>
                <button
                  onClick={() =>
                    setPage((p) =>
                      Math.min(Math.ceil(totalLogs / pageSize), p + 1)
                    )
                  }
                  disabled={page >= Math.ceil(totalLogs / pageSize)}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
