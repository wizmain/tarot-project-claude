# Tarot AI Reading Service - Frontend

Next.js 14 기반 타로 AI 리딩 서비스 프론트엔드

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **Linting**: ESLint + Prettier
- **Runtime**: React 18

## 프로젝트 구조

```
frontend/
├── src/
│   ├── app/              # App Router 페이지
│   │   ├── layout.tsx    # 루트 레이아웃
│   │   ├── page.tsx      # 홈페이지
│   │   └── globals.css   # 전역 스타일
│   ├── components/       # 재사용 가능한 컴포넌트
│   ├── lib/              # 유틸리티 함수
│   └── types/            # TypeScript 타입 정의
├── public/               # 정적 파일
├── package.json          # 의존성 관리
├── tsconfig.json         # TypeScript 설정
├── tailwind.config.ts    # Tailwind CSS 설정
└── next.config.js        # Next.js 설정
```

## 시작하기

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

```bash
# .env.local.example을 .env.local로 복사
cp .env.local.example .env.local

# 필요한 경우 환경 변수 수정
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 사용 가능한 스크립트

```bash
# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm run start

# 린팅 검사
npm run lint

# 코드 포맷팅
npm run format
```

## 페이지 구조

### 현재 구현된 페이지

- **홈페이지** (`/`) - 타로 리딩 서비스 소개 및 메인 네비게이션
- **원카드 리딩** (`/reading/one-card`) - 원카드 리딩 요청 및 결과
- **쓰리카드 리딩** (`/reading/three-card`) - 쓰리카드 리딩 요청 및 결과
- **리딩 히스토리** (`/history`) - 과거 리딩 기록 목록
- **리딩 상세** (`/history/detail`) - 개별 리딩 상세 보기 (id는 쿼리 파라미터)
- **카드 컬렉션** (`/cards`) - 78장 타로 카드 컬렉션 (검색, 필터링, 상세 정보)

### 향후 계획

- **사용자 인증** (`/login`, `/register`) - 로그인 및 회원가입
- **더 많은 스프레드** - Celtic Cross 등 추가 스프레드 타입
- **카드 북마크** - 즐겨찾는 카드 저장
- **리딩 공유** - 리딩 결과 공유 기능

## 컴포넌트 구조

```
src/components/
├── TarotCard.tsx              # 타로 카드 컴포넌트 (3D 플립, 정/역방향)
└── CardDeck.tsx               # 카드 덱 (셔플 애니메이션, 드로우)
```

### TarotCard 컴포넌트
- 3D 플립 애니메이션
- 정방향/역방향 표시
- 3가지 크기 (small, medium, large)
- 카드 이미지 표시 (SVG)
- 클릭 이벤트 지원

### CardDeck 컴포넌트
- 카드 섞기 애니메이션
- 순차적 카드 드로우
- 랜덤 역방향 결정 (30% 확률)
- 백엔드 API 통합

## 스타일링

### Tailwind CSS 사용

이 프로젝트는 Tailwind CSS를 사용하여 스타일링합니다.

```tsx
// 예시
<div className="flex items-center justify-center min-h-screen bg-gray-100">
  <h1 className="text-4xl font-bold text-blue-600">
    Tarot AI Reading
  </h1>
</div>
```

### 다크 모드 지원

Tailwind의 다크 모드를 활용합니다:

```tsx
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">
  컨텐츠
</div>
```

## API 통신

### API 클라이언트

```typescript
// src/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Cards API
export const cardAPI = {
  getCards: async (params) => { /* ... */ },
  getCard: async (cardId) => { /* ... */ },
};

// Readings API
export const readingAPI = {
  createReading: async (data) => { /* ... */ },
  getReadings: async (params) => { /* ... */ },
  getReading: async (readingId) => { /* ... */ },
};
```

## TypeScript

### 타입 정의

```typescript
// src/types/index.ts
export interface Card {
  id: string;
  name: string;
  name_ko: string;
  arcana_type: ArcanaType;
  suit?: Suit;
  number?: number;
  keywords_upright: string[];
  keywords_reversed: string[];
  meaning_upright: string;
  meaning_reversed: string;
  description?: string;
  symbolism?: string;
  image_url: string;
}

// src/types/reading.ts
export interface ReadingResponse {
  id: string;
  spread_type: string;
  question: string;
  summary: string;
  overall_reading: string;
  card_relationships?: string;
  advice: Advice;
  cards: ReadingCard[];
  created_at: string;
}
```

## 코드 품질

### ESLint

```bash
# 린팅 검사
npm run lint
```

### Prettier

```bash
# 코드 포맷팅
npm run format
```

### TypeScript

TypeScript strict 모드를 사용하여 타입 안정성을 보장합니다.

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API URL | http://localhost:8000 |

## 배포

### Vercel 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### 환경 변수 설정 (프로덕션)

Vercel 대시보드에서 다음 환경 변수를 설정:

- `NEXT_PUBLIC_API_URL`: 프로덕션 백엔드 API URL

## 현재 구현 상태

### ✅ 완료
- [x] Next.js 14 프로젝트 초기화 (App Router)
- [x] TypeScript 설정
- [x] Tailwind CSS 설정
- [x] ESLint + Prettier 설정
- [x] Framer Motion 애니메이션
- [x] 기본 레이아웃 구조
- [x] 홈페이지 UI
- [x] 타로 카드 UI 컴포넌트 (TarotCard)
- [x] 카드 덱 컴포넌트 (CardDeck)
- [x] 원카드 리딩 페이지 (전체 플로우)
- [x] 쓰리카드 리딩 페이지 (전체 플로우)
- [x] 리딩 히스토리 페이지 (목록, 필터링, 페이지네이션)
- [x] 리딩 상세 페이지 (동적 라우팅)
- [x] 카드 컬렉션 페이지 (검색, 필터링, 상세 모달)
- [x] API 통신 구현 (Cards, Readings)
- [x] TypeScript 타입 정의
- [x] 반응형 디자인
- [x] 다크 모드 지원

### 🚧 향후 계획
- [ ] 사용자 인증 페이지 (로그인, 회원가입)
- [ ] 더 많은 스프레드 타입
- [ ] 카드 북마크 기능
- [ ] 리딩 공유 기능
- [ ] 성능 최적화 (이미지, 코드 스플리팅)
- [ ] SEO 최적화
- [ ] PWA 지원

## 브라우저 지원

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 문서

- [프로젝트 기획](../PROJECT_PLAN.md)
- [의도 문서](../INTEND.md)
- [태스크 관리](../TASK.md)
- [백엔드 문서](../backend/README.md)

## 라이선스

MIT License
