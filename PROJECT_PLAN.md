# 타로 AI 리딩 서비스 프로젝트 기획

## 프로젝트 개요
AI 기술을 활용한 타로 카드 리딩 서비스
- 다중 AI 서비스 연동
- 고급 프롬프팅 엔진
- DSPy + GEPA 기반 학습 시스템

## 핵심 기능

### 1. 타로 카드 시스템
- **카드 데이터베이스**: 메이저 아르카나 22장 + 마이너 아르카나 56장 (총 78장)
- **카드 정보**: 각 카드별 정방향/역방향 의미, 이미지, 키워드, 상세 해석
- **카드 섞기 및 선택**: 랜덤 알고리즘으로 공정한 카드 선택

### 2. 스프레드(배열법) 종류
- **원카드**: 오늘의 운세, 간단한 질문
- **쓰리카드**: 과거-현재-미래 또는 상황-행동-결과
- **켈틱 크로스**: 10장 카드로 심층 분석
- **러브 스프레드**: 연애운 전용
- **커스텀 스프레드**: 사용자 정의 배열

### 3. 상담 유형
- **일반 운세**: 오늘/이번주/이번달 운세
- **카테고리별 상담**: 연애, 재물, 직업, 건강, 학업
- **구체적 질문**: 자유 형식 질문 입력

### 4. 결과 제공
- **카드 해석**: AI 기반 해석 제공
- **종합 리딩**: 선택된 카드들의 조합 해석
- **조언 및 가이드**: 실용적인 조언 제공
- **결과 저장**: 과거 점 기록 보관

### 5. 사용자 관리
- **회원가입/로그인**: 소셜 로그인 지원
- **프로필**: 생년월일, 별자리 등 개인정보
- **점 히스토리**: 과거 점 결과 조회
- **즐겨찾기**: 의미있는 결과 저장

### 6. 커뮤니티 (선택)
- **결과 공유**: SNS 공유 기능
- **상담 게시판**: 사용자간 해석 공유
- **전문가 상담**: 유료 1:1 상담 연결

## AI 시스템 아키텍처

### 1. Multi-AI Provider 연결 레이어

**지원 AI 서비스**
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic Claude (Sonnet, Opus)
- Google Gemini
- Cohere
- Local LLM (Ollama, LLaMA)

**AI Provider 추상화 계층**
```
AIProviderInterface
├── OpenAIProvider
├── ClaudeProvider
├── GeminiProvider
├── CohereProvider
└── LocalLLMProvider
```

**주요 기능**
- Provider switching (동적 AI 모델 전환)
- Fallback 메커니즘 (한 서비스 실패시 다른 서비스로 자동 전환)
- Load balancing (요청 분산)
- Cost tracking (AI 사용 비용 추적)
- Response caching (동일 질문 캐싱)

### 2. 타로 해석 프롬프팅 엔진

**프롬프트 구조**
```
System Prompt
├── 타로 전문가 페르소나
├── 카드 해석 원칙
└── 응답 형식 가이드

Context Builder
├── 선택된 카드 정보
├── 스프레드 타입
├── 사용자 질문
├── 사용자 컨텍스트 (생년월일, 과거 리딩)
└── 카드 조합 의미

Output Template
├── 카드별 해석
├── 종합 리딩
└── 조언 및 가이드
```

**프롬프트 버전 관리**
- 프롬프트 템플릿 DB 저장
- A/B 테스팅
- 성능 메트릭 추적
- 버전별 롤백 기능

### 3. DSPy + GEPA 학습 시스템

**DSPy (Declarative Self-improving Python) 구현**

**학습 파이프라인**
```
Data Collection
├── 사용자 피드백 (평점, 댓글)
├── 전문가 검수 데이터
└── 리딩 세션 로그

GEPA (Guided Exploration and Preference Alignment)
├── Exploration: 다양한 프롬프트 변형 생성
├── Evaluation: 사용자 선호도 측정
├── Alignment: 고평점 패턴 학습
└── Optimization: 프롬프트 개선

Feedback Loop
├── 긍정/부정 피드백 수집
├── 해석 품질 스코어링
├── 프롬프트 파라미터 조정
└── 자동 재학습
```

**학습 목표**
- 해석의 정확도 향상
- 사용자 만족도 증가
- 문화적 맥락 이해
- 개인화된 리딩 스타일

### 4. 시스템 구성도

```
[Frontend]
    ↓
[API Gateway]
    ↓
[타로 리딩 서비스]
    ├── [카드 선택 엔진]
    ├── [컨텍스트 빌더]
    └── [AI 오케스트레이터]
           ↓
    [프롬프트 엔진]
    ├── 템플릿 매니저
    ├── 컨텍스트 인젝터
    └── 프롬프트 옵티마이저 (DSPy)
           ↓
    [AI Provider Layer]
    ├── OpenAI
    ├── Claude
    ├── Gemini
    └── Others
           ↓
    [Response Processor]
    ├── 파싱
    ├── 검증
    └── 포맷팅
           ↓
    [Feedback System]
    ├── 피드백 수집
    ├── GEPA 학습
    └── 프롬프트 업데이트
```

## 기술 스택

### Frontend
- **웹**: React/Next.js + TypeScript + Tailwind CSS
- **모바일**: React Native 또는 Flutter
- **애니메이션**: Framer Motion (카드 뒤집기, 섞기 효과)

### Backend - Core
- **언어**: Python (AI/ML 생태계 활용)
- **Framework**: FastAPI (비동기, 고성능)
- **DSPy**: dspy-ai 라이브러리
- **LangChain**: AI 오케스트레이션 (선택)

### AI Integration
```python
# AI Provider SDK
- openai
- anthropic
- google-generativeai
- cohere
- litellm (통합 인터페이스)
```

### Database
- **PostgreSQL**: 사용자, 리딩 기록, 피드백
- **Vector DB** (Pinecone/Weaviate): 카드 임베딩, 의미 검색
- **Redis**: 프롬프트 캐싱, 세션 관리

### MLOps
- **Experiment Tracking**: Weights & Biases / MLflow
- **Prompt Management**: Langfuse / Helicone
- **Monitoring**: Prometheus + Grafana

### 인프라
- **호스팅**: Vercel/AWS/GCP
- **이미지 저장**: AWS S3 또는 Cloudinary
- **인증**: JWT + OAuth 2.0

## 프로젝트 구조

```
taro-ai-service/
├── src/
│   ├── ai/
│   │   ├── providers/          # AI 서비스 연결
│   │   ├── prompt_engine/      # 프롬프팅 엔진
│   │   └── dspy_optimizer/     # DSPy 학습 시스템
│   ├── tarot/
│   │   ├── cards/              # 카드 데이터
│   │   ├── spreads/            # 스프레드 로직
│   │   └── interpreter/        # 해석 로직
│   ├── feedback/               # GEPA 학습
│   ├── api/                    # REST API
│   └── models/                 # DB 모델
├── prompts/
│   ├── templates/              # 프롬프트 템플릿
│   └── versions/               # 버전 관리
├── data/
│   ├── cards.json              # 타로 카드 데이터
│   └── training/               # 학습 데이터
└── tests/
```

## 구현 로드맵

### Phase 1: MVP (2-3개월)
1. ✅ 프로젝트 기획 및 요구사항 정의
2. AI Provider 추상화 레이어 (OpenAI, Claude)
3. 기본 프롬프트 엔진
4. 타로 카드 데이터베이스 구축 (78장)
5. 원카드/쓰리카드 리딩 구현
6. 피드백 수집 시스템
7. 기본 웹 인터페이스

**MVP 목표**
- 사용자가 질문하고 타로 리딩 결과를 받을 수 있는 기본 기능
- 최소 2개 AI 모델 지원
- 피드백 수집 인프라 구축

### Phase 2: 최적화 (2-3개월)
1. DSPy 프롬프트 최적화 파이프라인
2. GEPA 학습 시스템 구축
3. 다중 AI 모델 지원 확대 (Gemini, Cohere)
4. Vector DB를 활용한 의미 검색
5. 켈틱 크로스 등 고급 스프레드 추가
6. 프롬프트 A/B 테스팅 시스템
7. 성능 모니터링 대시보드

**Phase 2 목표**
- AI 응답 품질 자동 개선
- 사용자 만족도 80% 이상
- 응답 시간 3초 이내

### Phase 3: 고도화 (3-4개월)
1. 개인화된 리딩 (사용자 히스토리 기반)
2. 실시간 학습 및 프롬프트 업데이트
3. A/B 테스팅 자동화
4. 모바일 앱 개발
5. 프리미엄 기능 (무제한 리딩, 전문가 상담)
6. 커뮤니티 기능
7. 다국어 지원

**Phase 3 목표**
- 개인화된 사용자 경험
- 월간 활성 사용자 10,000명
- 수익화 모델 안정화

## 추가 기능 (향후 확장)

### 프리미엄 기능
- **무제한 점**: 일일 점 횟수 제한 해제
- **상세 리딩**: 더 깊은 해석 제공
- **전문가 상담**: 실제 타로 리더와 연결
- **광고 제거**

### 게이미피케이션
- **일일 출석**: 매일 무료 원카드
- **레벨 시스템**: 점 횟수로 레벨업
- **배지/업적**: 특정 조건 달성시 보상
- **포인트 시스템**: 활동으로 포인트 획득

### UX 강화
- **아름다운 카드 디자인**: 여러 덱 스타일 선택
- **몰입형 애니메이션**: 카드 선택시 실감나는 효과
- **사운드 효과**: 카드 섞기, 뒤집기 소리
- **다크모드**: 신비로운 분위기 연출

## 성공 지표 (KPI)

### 사용자 지표
- 일간/월간 활성 사용자 (DAU/MAU)
- 사용자 유지율 (Retention Rate)
- 평균 세션 시간
- 리딩당 평균 만족도 점수

### 기술 지표
- AI 응답 품질 스코어
- 평균 응답 시간
- 시스템 가용성 (Uptime)
- API 에러율

### 비즈니스 지표
- 프리미엄 전환율
- 월간 반복 수익 (MRR)
- 사용자당 평균 수익 (ARPU)
- 고객 생애 가치 (LTV)

## 리스크 및 고려사항

### 기술적 리스크
- AI 서비스 비용 증가
- AI 응답 품질 관리
- 시스템 확장성

### 비즈니스 리스크
- 사용자 획득 비용
- 경쟁 서비스 출현
- 법적/윤리적 이슈 (점술 관련 규제)

### 대응 방안
- Multi-provider 아키텍처로 비용 최적화
- 지속적인 품질 모니터링 및 학습
- 단계적 확장 및 성능 테스트
- 명확한 서비스 이용약관 및 책임 한계 고지

## 다음 단계

1. 상세 기술 스펙 문서 작성
2. 타로 카드 데이터 수집 및 구조화
3. AI 프롬프트 초안 작성
4. MVP 개발 시작
5. 베타 테스터 모집 및 피드백 수집

---

**문서 생성일**: 2025-10-18
**버전**: 1.0
**작성자**: Project Planning Session
