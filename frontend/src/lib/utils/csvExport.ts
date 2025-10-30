/**
 * CSV Export Utilities
 *
 * 이 모듈의 목적:
 * - Analytics 데이터를 CSV 형식으로 변환
 * - 브라우저에서 CSV 파일 다운로드
 * - 한글 인코딩 지원 (UTF-8 BOM)
 */

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
  by_model: Array<{
    model: string;
    provider: string;
    calls: number;
    total_cost: number;
    avg_latency: number;
  }>;
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

/**
 * CSV 문자열로 변환 (쉼표와 따옴표 처리)
 */
function escapeCSV(value: any): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  // 쉼표, 따옴표, 줄바꿈이 있으면 따옴표로 감싸기
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * CSV 파일 다운로드
 */
function downloadCSV(content: string, filename: string) {
  // UTF-8 BOM 추가 (Excel에서 한글 제대로 표시)
  const BOM = "\uFEFF";
  const blob = new Blob([BOM + content], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Summary 데이터를 CSV로 export
 */
export function exportSummaryToCSV(data: SummaryData) {
  const headers = [
    "항목",
    "값",
    "이전 기간 대비 변화율(%)",
  ];

  const rows = [
    ["총 비용 (USD)", `$${data.total_cost.toFixed(4)}`, data.comparison.cost_change_percent.toFixed(1)],
    ["총 호출 수", data.total_calls.toString(), data.comparison.calls_change_percent.toFixed(1)],
    ["평균 응답 시간 (초)", data.avg_latency_seconds.toFixed(2), data.comparison.latency_change_percent.toFixed(1)],
    ["집계 기간 (일)", data.period_days.toString(), "-"],
  ];

  // 모델별 통계 추가
  rows.push([]);
  rows.push(["모델별 통계", "", ""]);
  rows.push(["Provider", "Model", "호출 수", "비용 (USD)", "평균 응답시간 (초)"]);

  data.by_model.forEach((model) => {
    rows.push([
      model.provider,
      model.model,
      model.calls.toString(),
      `$${model.total_cost.toFixed(4)}`,
      model.avg_latency.toFixed(2),
    ]);
  });

  const csvContent =
    headers.map(escapeCSV).join(",") +
    "\n" +
    rows.map((row) => row.map(escapeCSV).join(",")).join("\n");

  const timestamp = new Date().toISOString().split("T")[0];
  downloadCSV(csvContent, `llm_usage_summary_${timestamp}.csv`);
}

/**
 * Daily Trend 데이터를 CSV로 export
 */
export function exportDailyTrendToCSV(data: DailyTrendData[]) {
  const headers = ["날짜", "총 비용 (USD)", "총 호출 수", "평균 응답시간 (초)"];

  const rows = data.map((item) => [
    item.date,
    `$${item.total_cost.toFixed(4)}`,
    item.total_calls.toString(),
    item.avg_latency.toFixed(2),
  ]);

  const csvContent =
    headers.map(escapeCSV).join(",") +
    "\n" +
    rows.map((row) => row.map(escapeCSV).join(",")).join("\n");

  const timestamp = new Date().toISOString().split("T")[0];
  downloadCSV(csvContent, `llm_usage_daily_trend_${timestamp}.csv`);
}

/**
 * Recent Logs를 CSV로 export
 */
export function exportRecentLogsToCSV(data: RecentLogEntry[]) {
  const headers = [
    "생성 시간",
    "Provider",
    "Model",
    "Prompt 토큰",
    "Completion 토큰",
    "총 토큰",
    "비용 (USD)",
    "응답 시간 (초)",
    "목적",
    "질문",
  ];

  const rows = data.map((log) => [
    new Date(log.created_at).toLocaleString("ko-KR"),
    log.provider,
    log.model,
    log.prompt_tokens.toString(),
    log.completion_tokens.toString(),
    log.total_tokens.toString(),
    `$${log.estimated_cost.toFixed(4)}`,
    log.latency_seconds.toFixed(2),
    log.purpose,
    log.reading_question || "-",
  ]);

  const csvContent =
    headers.map(escapeCSV).join(",") +
    "\n" +
    rows.map((row) => row.map(escapeCSV).join(",")).join("\n");

  const timestamp = new Date().toISOString().split("T")[0];
  downloadCSV(csvContent, `llm_usage_recent_logs_${timestamp}.csv`);
}
