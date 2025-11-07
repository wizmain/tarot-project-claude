'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { config } from '@/config/env';

interface LLMProvider {
  name: string;
  api_key: string;
  model: string;
  enabled: boolean;
  timeout: number;
}

interface AppSettings {
  admin: {
    admin_emails: string[];
  };
  ai: {
    provider_priority: string[];
    providers: LLMProvider[];
    default_timeout: number;
  };
  updated_at: string | null;
  updated_by: string | null;
}

function AdminSettingsContent() {
  const router = useRouter();
  const { accessToken } = useAuth();

  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Form states
  const [adminEmails, setAdminEmails] = useState<string[]>([]);
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [providerPriority, setProviderPriority] = useState<string[]>([]);
  const [providers, setProviders] = useState<LLMProvider[]>([]);

  // Provider modal states
  const [showAddProviderModal, setShowAddProviderModal] = useState(false);
  const [newProvider, setNewProvider] = useState<LLMProvider>({
    name: 'openai',
    api_key: '',
    model: 'gpt-4o-mini',
    enabled: true,
    timeout: 30,
  });

  // Provider 이름 변경시 기본 모델도 변경
  const handleProviderNameChange = (providerName: string) => {
    const defaultModels: Record<string, string> = {
      'openai': 'gpt-4o-mini',
      'anthropic': 'claude-3-5-sonnet-20241022',
      'gemini': 'gemini-2.0-flash-exp',
    };
    
    setNewProvider({
      ...newProvider,
      name: providerName,
      model: defaultModels[providerName] || 'gpt-4o-mini',
    });
  };

  const fetchSettings = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${config.apiUrl}/api/v1/settings`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('관리자 권한이 필요합니다');
        }
        throw new Error('설정을 불러오는데 실패했습니다');
      }

      const data = await response.json();
      setSettings(data);
      setAdminEmails(data.admin.admin_emails);
      setProviderPriority(data.ai.provider_priority);
      setProviders(data.ai.providers);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      setError(err instanceof Error ? err.message : '설정을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleAddAdmin = async () => {
    if (!newAdminEmail || !accessToken) return;

    try {
      const response = await fetch(
        `${config.apiUrl}/api/v1/settings/admin/emails/${encodeURIComponent(newAdminEmail)}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('관리자 추가 실패');
      }

      setNewAdminEmail('');
      await fetchSettings();
    } catch (err) {
      alert(err instanceof Error ? err.message : '관리자 추가 실패');
    }
  };

  const handleRemoveAdmin = async (email: string) => {
    if (!accessToken) return;
    
    if (!confirm(`'${email}'을(를) 관리자 목록에서 제거하시겠습니까?`)) {
      return;
    }

    try {
      const response = await fetch(
        `${config.apiUrl}/api/v1/settings/admin/emails/${encodeURIComponent(email)}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '관리자 제거 실패');
      }

      await fetchSettings();
    } catch (err) {
      alert(err instanceof Error ? err.message : '관리자 제거 실패');
    }
  };

  const handleAddProvider = async () => {
    if (!accessToken || !newProvider.api_key) {
      alert('API Key를 입력해주세요');
      return;
    }

    try {
      setSaving(true);

      const response = await fetch(`${config.apiUrl}/api/v1/settings/ai/providers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(newProvider),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Provider 추가 실패');
      }

      setShowAddProviderModal(false);
      setNewProvider({
        name: 'openai',
        api_key: '',
        model: 'gpt-4o-mini',
        enabled: true,
        timeout: 30,
      });
      await fetchSettings();
      alert('✅ Provider가 추가되었습니다.\n변경사항이 다음 리딩부터 즉시 적용됩니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Provider 추가 실패');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteProvider = async (providerName: string) => {
    if (!accessToken) return;
    
    if (!confirm(`'${providerName}' Provider를 삭제하시겠습니까?`)) {
      return;
    }

    try {
      setSaving(true);

      const response = await fetch(
        `${config.apiUrl}/api/v1/settings/ai/providers/${encodeURIComponent(providerName)}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Provider 삭제 실패');
      }

      await fetchSettings();
      alert('✅ Provider가 삭제되었습니다.\n변경사항이 다음 리딩부터 즉시 적용됩니다.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Provider 삭제 실패');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleProvider = async (providerName: string) => {
    if (!accessToken) return;

    try {
      setSaving(true);

      const response = await fetch(
        `${config.apiUrl}/api/v1/settings/ai/providers/${encodeURIComponent(providerName)}/toggle`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Provider 토글 실패');
      }

      await fetchSettings();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Provider 토글 실패');
    } finally {
      setSaving(false);
    }
  };

  const handleMovePriority = async (index: number, direction: 'up' | 'down') => {
    if (!accessToken) return;

    const newPriority = [...providerPriority];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newPriority.length) {
      return;
    }

    // Swap
    [newPriority[index], newPriority[targetIndex]] = [
      newPriority[targetIndex],
      newPriority[index],
    ];

    try {
      setSaving(true);

      const response = await fetch(`${config.apiUrl}/api/v1/settings/ai/providers/priority`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(newPriority),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '우선순위 변경 실패');
      }

      await fetchSettings();
    } catch (err) {
      alert(err instanceof Error ? err.message : '우선순위 변경 실패');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAISettings = async () => {
    if (!accessToken) return;

    try {
      setSaving(true);

      const response = await fetch(`${config.apiUrl}/api/v1/settings/ai`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          provider_priority: providerPriority,
          providers: providers,
          default_timeout: settings?.ai.default_timeout || 30,
        }),
      });

      if (!response.ok) {
        throw new Error('AI 설정 저장 실패');
      }

      alert('설정이 저장되었습니다');
      await fetchSettings();
    } catch (err) {
      alert(err instanceof Error ? err.message : '설정 저장 실패');
    } finally {
      setSaving(false);
    }
  };

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
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/admin')}
            className="mb-4 text-purple-600 dark:text-purple-400 hover:underline"
          >
            ← 관리자 대시보드로
          </button>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            ⚙️ 시스템 설정
          </h1>
        </div>

        {/* Admin Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            👨‍💼 관리자 설정
          </h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              관리자 이메일 추가
            </label>
            <div className="flex gap-2">
              <input
                type="email"
                value={newAdminEmail}
                onChange={(e) => setNewAdminEmail(e.target.value)}
                placeholder="admin@example.com"
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <button
                onClick={handleAddAdmin}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
              >
                추가
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              현재 관리자 목록 ({adminEmails.length}명)
            </h3>
            <ul className="space-y-2">
              {adminEmails.map((email) => (
                <li
                  key={email}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded"
                >
                  <span className="text-gray-900 dark:text-white">{email}</span>
                  <button
                    onClick={() => handleRemoveAdmin(email)}
                    disabled={adminEmails.length <= 1}
                    className={`text-sm px-3 py-1 rounded transition-all ${
                      adminEmails.length <= 1
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700'
                    }`}
                    title={
                      adminEmails.length <= 1
                        ? '최소 1명의 관리자가 필요합니다'
                        : '관리자 제거'
                    }
                  >
                    {adminEmails.length <= 1 ? '🔒 제거 불가' : '🗑️ 제거'}
                  </button>
                </li>
              ))}
            </ul>
            {adminEmails.length <= 1 && (
              <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                ⚠️ 최소 1명의 관리자가 필요합니다. 다른 관리자를 추가한 후 제거할 수 있습니다.
              </p>
            )}
          </div>
        </div>

        {/* AI Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            🤖 AI Provider 설정
          </h2>

          {/* Provider Priority */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Provider 우선순위
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              💡 위에 있을수록 먼저 시도됩니다. 화살표로 순서를 변경하세요.
            </p>
            <div className="space-y-2">
              {providerPriority.map((providerName, index) => (
                <div
                  key={providerName}
                  className="flex items-center gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg"
                >
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => handleMovePriority(index, 'up')}
                      disabled={index === 0 || saving}
                      className={`p-1 rounded transition-all ${
                        index === 0 || saving
                          ? 'text-gray-300 cursor-not-allowed'
                          : 'text-purple-600 hover:bg-purple-100 dark:hover:bg-purple-800'
                      }`}
                      title="위로 이동"
                    >
                      ⬆️
                    </button>
                    <button
                      onClick={() => handleMovePriority(index, 'down')}
                      disabled={index === providerPriority.length - 1 || saving}
                      className={`p-1 rounded transition-all ${
                        index === providerPriority.length - 1 || saving
                          ? 'text-gray-300 cursor-not-allowed'
                          : 'text-purple-600 hover:bg-purple-100 dark:hover:bg-purple-800'
                      }`}
                      title="아래로 이동"
                    >
                      ⬇️
                    </button>
                  </div>
                  <div className="flex-1">
                    <span className="font-medium text-purple-800 dark:text-purple-200">
                      {index + 1}. {providerName}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Provider List */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Provider 목록 ({providers.length}개)
              </h3>
              <button
                onClick={() => setShowAddProviderModal(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all text-sm"
              >
                ➕ Provider 추가
              </button>
            </div>
            
            {providers.length === 0 ? (
              <div className="p-8 text-center bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-gray-500 dark:text-gray-400">
                  등록된 Provider가 없습니다. Provider를 추가해주세요.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {providers.map((provider) => (
                  <div
                    key={provider.name}
                    className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-2 border-transparent hover:border-purple-300 dark:hover:border-purple-600 transition-all"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <p className="font-semibold text-lg text-gray-900 dark:text-white">
                          📦 {provider.name}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Model: <span className="font-mono">{provider.model}</span>
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 font-mono mt-1">
                          API Key: {provider.api_key}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Timeout: {provider.timeout}초
                        </p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={provider.enabled}
                            onChange={() => handleToggleProvider(provider.name)}
                            disabled={saving}
                            className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                          />
                          <span
                            className={`text-sm font-medium ${
                              provider.enabled
                                ? 'text-green-600 dark:text-green-400'
                                : 'text-gray-500'
                            }`}
                          >
                            {provider.enabled ? '✓ 활성화' : '✗ 비활성화'}
                          </span>
                        </label>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={() => handleDeleteProvider(provider.name)}
                        disabled={saving}
                        className="px-3 py-1 bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700 rounded text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        🗑️ 삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Add Provider Modal */}
        {showAddProviderModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                ➕ Provider 추가
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Provider 이름
                  </label>
                  <select
                    value={newProvider.name}
                    onChange={(e) => handleProviderNameChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    API Key *
                  </label>
                  <input
                    type="password"
                    value={newProvider.api_key}
                    onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                    placeholder="sk-..."
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Model
                  </label>
                  <input
                    type="text"
                    value={newProvider.model}
                    onChange={(e) => setNewProvider({ ...newProvider, model: e.target.value })}
                    placeholder={
                      newProvider.name === 'openai' ? 'gpt-4o-mini' :
                      newProvider.name === 'anthropic' ? 'claude-3-5-sonnet-20241022' :
                      newProvider.name === 'gemini' ? 'gemini-2.0-flash-exp' :
                      'model-name'
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Timeout (초)
                  </label>
                  <input
                    type="number"
                    value={newProvider.timeout}
                    onChange={(e) => setNewProvider({ ...newProvider, timeout: parseInt(e.target.value) })}
                    min="5"
                    max="120"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newProvider.enabled}
                    onChange={(e) => setNewProvider({ ...newProvider, enabled: e.target.checked })}
                    className="w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                  />
                  <label className="text-sm text-gray-700 dark:text-gray-300">
                    활성화
                  </label>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowAddProviderModal(false);
                    setNewProvider({
                      name: 'openai',
                      api_key: '',
                      model: 'gpt-4o-mini',
                      enabled: true,
                      timeout: 30,
                    });
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-900 dark:text-white rounded-lg font-semibold transition-all"
                >
                  취소
                </button>
                <button
                  onClick={handleAddProvider}
                  disabled={saving || !newProvider.api_key}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition-all"
                >
                  {saving ? '추가 중...' : '추가'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

export default function AdminSettings() {
  return (
    <ProtectedRoute>
      <AdminSettingsContent />
    </ProtectedRoute>
  );
}

