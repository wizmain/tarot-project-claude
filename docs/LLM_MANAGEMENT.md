# 병렬 처리 LLM 관리 방안

## 개요

병렬 처리 시 여러 LLM을 효율적으로 관리하기 위한 전략과 구현 방안을 설명합니다.

## 현재 구현

### 1. LLM 할당 전략 (`LLMAllocator`)

작업 유형별로 최적의 모델을 선택합니다:

- **카드 해석** (`card_interpretation`): 빠르고 저렴한 모델 (예: `claude-haiku`)
- **종합 리딩** (`overall_reading`): 고성능 모델 (예: `claude-sonnet`)
- **관계 분석** (`relationships`): 중간 성능 모델
- **조언** (`advice`): 중간 성능 모델

```python
from src.ai.prompt_engine.llm_allocation import get_allocator

allocator = get_allocator()
config = allocator.get_config("card_interpretation")
# config.model, config.max_tokens, config.temperature 사용
```

### 2. 동시 호출 수 제한 (Rate Limiting)

`SpreadConfig`의 `max_concurrent_calls` 필드로 스프레드별 동시 호출 수를 제한합니다:

```python
# spread_config.py
"celtic_cross": SpreadConfig(
    ...
    max_concurrent_calls=5  # 동시에 최대 5개의 LLM 호출 허용
)
```

`ParallelReadingEngine`은 `asyncio.Semaphore`를 사용하여 동시 호출 수를 제한합니다:

```python
# parallel_reading_engine.py
self.semaphore = asyncio.Semaphore(max_concurrent)

# LLM 호출 시
async with self.semaphore:
    response = await self.orchestrator.generate(...)
```

### 3. 스프레드별 설정 통합

모든 스프레드 설정은 `spread_config.py`에서 중앙 관리됩니다:

- `card_count`: 카드 수
- `positions`: 포지션 정보
- `batch_size`: 배치 크기
- `max_concurrent_calls`: 동시 호출 수 제한
- `max_tokens`: 최대 토큰 수

## 확장성 고려 사항

### 1. 스프레드별 LLM 할당 전략

현재는 전역 `LLMAllocator`를 사용하지만, 필요시 스프레드별 할당 전략을 추가할 수 있습니다:

```python
# 향후 확장 예시
@dataclass
class SpreadConfig:
    ...
    llm_allocation: Optional[Dict[str, ModelConfig]] = None  # 스프레드별 할당 전략
```

### 2. 동적 할당 전략

환경 변수나 데이터베이스 설정을 통해 런타임에 할당 전략을 변경할 수 있습니다:

```python
# llm_allocation.py
def _apply_env_overrides(self):
    """환경 변수에서 설정 오버라이드"""
    # 예: CELTIC_CROSS_CARD_MODEL=claude-haiku-20240307
    # 예: CELTIC_CROSS_OVERALL_MODEL=claude-sonnet-4-20250514
```

### 3. LLM 풀 관리

대규모 병렬 처리 시 LLM 인스턴스 풀을 관리할 수 있습니다:

```python
# 향후 확장 예시
class LLMPool:
    """LLM 인스턴스 풀 관리"""
    def __init__(self, max_size: int = 10):
        self.pool = asyncio.Queue(maxsize=max_size)
        self.max_size = max_size
    
    async def acquire(self) -> AIOrchestrator:
        """풀에서 오케스트레이터 가져오기"""
        return await self.pool.get()
    
    async def release(self, orchestrator: AIOrchestrator):
        """오케스트레이터를 풀에 반환"""
        await self.pool.put(orchestrator)
```

## 성능 최적화

### 1. 배치 크기 조정

스프레드별로 최적의 배치 크기를 설정:

```python
"celtic_cross": SpreadConfig(
    batch_size=3,  # 10장을 3-3-3-1로 분할
)
```

### 2. 병렬 처리 단계 최적화

Phase 1 (카드 해석)과 Phase 2 (종합, 관계, 조언)를 분리하여 효율성 향상:

- Phase 1: 모든 카드 배치를 병렬 처리
- Phase 2: 종합 리딩과 관계 분석을 병렬 처리 후, 조언 생성

### 3. Rate Limiting 전략

API Rate Limit을 고려한 동시 호출 수 제한:

- 기본값: 5개 동시 호출
- 스프레드별로 조정 가능
- 환경 변수로 오버라이드 가능

## 모니터링 및 로깅

### 1. LLM 사용량 추적

각 LLM 호출의 정보를 로깅:

```python
logger.info(
    f"Allocated model {config.model} for task {task_type} "
    f"(max_tokens={config.max_tokens}, temp={config.temperature})"
)
```

### 2. 성능 메트릭

병렬 처리 성능을 추적:

- 총 처리 시간
- 병렬 처리로 인한 시간 절감
- 동시 호출 수
- Rate Limit 도달 횟수

## 향후 개선 방안

1. **스프레드별 LLM 할당 전략**: 각 스프레드에 최적화된 모델 선택
2. **동적 Rate Limiting**: API 응답 시간에 따라 동적으로 조정
3. **LLM 풀 관리**: 대규모 병렬 처리 시 인스턴스 재사용
4. **비용 최적화**: 작업 유형별 비용 추적 및 최적화
5. **자동 Fallback**: 모델 실패 시 자동으로 다른 모델로 전환

## 사용 예시

### 새로운 스프레드 추가 시

```python
# spread_config.py
"horoscope": SpreadConfig(
    spread_type="horoscope",
    card_count=12,
    positions=[...],
    supports_parallel=True,
    batch_size=4,  # 12장을 3개 배치로 (4장씩)
    max_concurrent_calls=6,  # 호로스코프는 더 많은 동시 호출 허용
    parallel_templates={
        "card": "reading/horoscope_card.txt",
        "overall": "reading/horoscope_overall.txt",
    },
    max_tokens=4096
)
```

코드 수정 없이 설정만 추가하면 자동으로 병렬 처리됩니다.

