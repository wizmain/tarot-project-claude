# SSE (Server-Sent Events) 구현 가이드

## 개요

타로 리딩 생성 과정을 실시간으로 스트리밍하는 SSE 기반 시스템입니다.

## 구현된 파일

### 1. SSE 클라이언트 (`src/lib/sse-client.ts`)

타입 안전한 SSE 클라이언트로, 백엔드의 SSE 이벤트를 처리합니다.

**주요 클래스:**
- `SSEReadingClient`: SSE 연결 및 이벤트 처리

**지원 이벤트:**
- `started`: 리딩 시작
- `progress`: 진행률 업데이트 (0-100%)
- `card_drawn`: 카드 뽑힘
- `rag_enrichment`: RAG 컨텍스트 로드 완료
- `ai_generation`: AI 생성 시작
- `complete`: 리딩 완료
- `error`: 오류 발생

### 2. React Hook (`src/lib/use-sse-reading.ts`)

SSE 연결 상태를 관리하는 커스텀 훅입니다.

**사용법:**
```typescript
const {
  isStreaming,
  progress,
  stage,
  message,
  drawnCards,
  readingId,
  error,
  totalTime,
  startReading,
  reset,
} = useSSEReading(API_URL, accessToken);
```

### 3. 진행률 UI 컴포넌트 (`src/components/ReadingProgress.tsx`)

실시간 진행 상황을 시각화하는 컴포넌트입니다.

**기능:**
- 단계별 이모지 표시
- 애니메이션 진행률 바
- 뽑힌 카드 목록
- 에러 메시지 표시

## 사용 예시

### 기본 사용법

```typescript
'use client';

import { useState } from 'react';
import { useSSEReading } from '@/lib/use-sse-reading';
import ReadingProgress from '@/components/ReadingProgress';
import { useRouter } from 'next/navigation';

export default function ReadingPage() {
  const router = useRouter();
  const [question, setQuestion] = useState('');

  const {
    isStreaming,
    progress,
    stage,
    message,
    drawnCards,
    readingId,
    error,
    startReading,
    reset,
  } = useSSEReading(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    'YOUR_ACCESS_TOKEN' // From auth context
  );

  const handleSubmit = async () => {
    await startReading({
      spread_type: 'one_card',
      question: question,
      category: 'general',
    });
  };

  // Redirect to reading result when complete
  useEffect(() => {
    if (readingId) {
      router.push(`/readings/${readingId}`);
    }
  }, [readingId, router]);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">타로 리딩</h1>

      {!isStreaming && !readingId && (
        <div className="max-w-2xl mx-auto">
          <textarea
            className="w-full p-4 border rounded-lg"
            rows={4}
            placeholder="질문을 입력하세요..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            className="mt-4 px-6 py-3 bg-purple-600 text-white rounded-lg"
            onClick={handleSubmit}
            disabled={!question}
          >
            리딩 시작
          </button>
        </div>
      )}

      <ReadingProgress
        isStreaming={isStreaming}
        progress={progress}
        stage={stage}
        message={message}
        drawnCards={drawnCards}
        error={error}
      />
    </div>
  );
}
```

### Auth Context와 통합

```typescript
import { useAuth } from '@/contexts/AuthContext';

export default function ReadingPage() {
  const { user, accessToken } = useAuth();

  const sse = useSSEReading(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    accessToken || ''
  );

  // ... rest of component
}
```

## 이벤트 흐름

```
1. [0%] Started
   ↓
2. [10%] Drawing Cards - 카드 선택 시작
   ↓
3. [10-30%] Card Drawn × N - 각 카드 뽑힘
   ↓
4. [35%] RAG Enrichment - 지식 검색 시작
   ↓
5. [50%] RAG Complete - 지식 검색 완료
   ↓
6. [60%] AI Generation - AI 리딩 생성 시작
   ↓
7. [80%] AI Complete - AI 생성 완료
   ↓
8. [90%] Saving - 데이터베이스 저장
   ↓
9. [100%] Complete - 리딩 완료 (reading_id 반환)
```

## 에러 처리

### 연결 에러
```typescript
onConnectionError: (error) => {
  console.error('SSE 연결 실패:', error);
  // 재시도 로직 또는 사용자에게 알림
}
```

### 서버 에러
```typescript
onError: (data) => {
  console.error('서버 오류:', data.message);
  // 에러 메시지 표시
}
```

## 성능 고려사항

1. **메모리 관리**: 컴포넌트 unmount 시 SSE 연결 종료
2. **재연결**: 연결 끊김 시 자동 재시도 (선택사항)
3. **타임아웃**: 120초 이후 자동 종료 (백엔드 설정)

## 테스트

### 수동 테스트
1. 프론트엔드 실행: `npm run dev`
2. 백엔드 실행: `python main.py`
3. 로그인 후 리딩 페이지 접속
4. 질문 입력 후 리딩 시작
5. 실시간 진행 상황 확인

### 개발자 도구
브라우저 Network 탭에서 `text/event-stream` 타입 요청 확인

## 향후 개선 사항

- [ ] 재연결 로직 추가
- [ ] SSE 연결 상태 모니터링
- [ ] 오프라인 처리
- [ ] 더 세밀한 진행률 단계
- [ ] 카드 드로우 애니메이션 강화
