'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { config } from '@/config/env';

interface DashboardStats {
  total_users: number;
  total_readings: number;
  total_feedback: number;
  avg_rating: number;
  total_cost: number;
  readings_today: number;
  readings_this_week: number;
  readings_this_month: number;
}

function AdminDashboardContent() {
  const router = useRouter();
  const { accessToken } = useAuth();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard stats
      const statsResponse = await fetch(`${config.apiUrl}/api/v1/admin/dashboard`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!statsResponse.ok) {
        if (statsResponse.status === 403) {
          throw new Error('관리자 권한이 필요합니다');
        }
        throw new Error('대시보드 통계를 불러오는데 실패했습니다');
      }

      const statsData = await statsResponse.json();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  const handleClearCache = async () => {
    if (!confirm('💡 모든 캐시를 초기화하시겠습니까?\n\n- AI Provider 설정이 다음 리딩부터 즉시 반영됩니다.\n- 현재 진행 중인 리딩에는 영향을 주지 않습니다.')) {
      return;
    }
    
    try {
      const response = await fetch(
        `${config.apiUrl}/api/v1/admin/cache/invalidate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            cache_types: ['all']
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error('캐시 초기화 실패');
      }
      
      const result = await response.json();
      alert(`✅ 캐시 초기화 완료!\n\n무효화된 캐시: ${result.invalidated.join(', ')}\n\n다음 리딩부터 새로운 설정이 적용됩니다.`);
    } catch (err) {
      console.error('Cache clear failed:', err);
      alert('❌ 캐시 초기화 중 오류가 발생했습니다.');
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center">
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
            >
              홈으로 돌아가기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/')}
            className="mb-4 text-purple-600 dark:text-purple-400 hover:underline"
          >
            ← 홈으로 돌아가기
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                🔧 관리자 대시보드
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                시스템 통계를 확인합니다
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/admin/settings')}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
              >
                ⚙️ 설정 관리
              </button>
              <button
                onClick={() => router.push('/analytics')}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold transition-all"
              >
                🤖 LLM 분석
              </button>
              <button
                onClick={handleClearCache}
                className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold transition-all"
                title="설정 변경 후 즉시 적용하려면 캐시를 초기화하세요"
              >
                🔄 캐시 초기화
              </button>
            </div>
          </div>
        </div>

        {/* Dashboard Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="총 사용자"
              value={stats.total_users}
              icon="👥"
              color="blue"
            />
            <StatCard
              title="총 리딩"
              value={stats.total_readings}
              icon="🎴"
              color="purple"
            />
            <StatCard
              title="총 피드백"
              value={stats.total_feedback}
              icon="💬"
              color="green"
            />
            <StatCard
              title="평균 평점"
              value={stats.avg_rating.toFixed(1)}
              suffix="/ 5.0"
              icon="⭐"
              color="yellow"
            />
            <StatCard
              title="총 LLM 비용"
              value={`$${stats.total_cost.toFixed(2)}`}
              icon="💰"
              color="red"
            />
            <StatCard
              title="오늘 리딩"
              value={stats.readings_today}
              icon="📅"
              color="indigo"
            />
            <StatCard
              title="이번 주 리딩"
              value={stats.readings_this_week}
              icon="📊"
              color="teal"
            />
            <StatCard
              title="이번 달 리딩"
              value={stats.readings_this_month}
              icon="📈"
              color="pink"
            />
          </div>
        )}
      </div>
    </main>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  suffix?: string;
  icon: string;
  color: 'blue' | 'purple' | 'green' | 'yellow' | 'red' | 'indigo' | 'teal' | 'pink';
}

function StatCard({ title, value, suffix, icon, color }: StatCardProps) {
  const colorClasses: Record<StatCardProps['color'], string> = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    yellow: 'from-yellow-500 to-yellow-600',
    red: 'from-red-500 to-red-600',
    indigo: 'from-indigo-500 to-indigo-600',
    teal: 'from-teal-500 to-teal-600',
    pink: 'from-pink-500 to-pink-600',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="flex items-baseline">
        <p className={`text-3xl font-bold bg-gradient-to-r ${colorClasses[color]} bg-clip-text text-transparent`}>
          {value}
        </p>
        {suffix && (
          <span className="ml-2 text-sm text-gray-500">{suffix}</span>
        )}
      </div>
    </motion.div>
  );
}

export default function AdminDashboard() {
  return (
    <ProtectedRoute>
      <AdminDashboardContent />
    </ProtectedRoute>
  );
}

