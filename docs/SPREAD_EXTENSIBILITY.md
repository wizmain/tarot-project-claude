# 스프레드 확장성 개선 문서

## 개선 사항 요약

새로운 리딩 타입(호로스코프, 호스슈 등) 추가 시 중복 코드 없이 확장 가능하도록 구조를 개선했습니다.

## 주요 변경 사항

### 1. 스프레드 설정 중앙화 (`spread_config.py`)

**이전**: 각 파일에 하드코딩된 스프레드 정보
```python
# readings_stream.py
card_count_map = {
    "one_card": 1,
    "three_card_past_present_future": 3,
    "celtic_cross": 10,
}
```

**개선**: 중앙화된 설정 관리
```python
# spread_config.py
SPREAD_CONFIGS = {
    "celtic_cross": SpreadConfig(
        spread_type="celtic_cross",
        card_count=10,
        positions=[...],
        supports_parallel=True,
        parallel_templates={...}
    )
}
```

**장점**:
- 새로운 스프레드 추가 시 `SPREAD_CONFIGS`에만 설정 추가
- 카드 수, 포지션 정보, 프롬프트 경로 등 모든 설정이 한 곳에 집중
- 병렬 처리 지원 여부도 설정으로 관리

### 2. ParallelReadingEngine 추상화

**이전**: 켈틱 크로스에만 특화
```python
# 하드코딩된 포지션 정보
CELTIC_CROSS_POSITIONS = [...]
template_name = f"reading/celtic_cross_card{lang_suffix}.txt"
if len(drawn_cards) != 10:
    raise ValueError("Celtic Cross requires exactly 10 cards")
```

**개선**: 스프레드 타입에 독립적
```python
# 스프레드 설정 기반 동적 처리
self.spread_config = get_spread_config(spread_type)
template_base = self.spread_config.parallel_templates.get("card")
expected_count = self.spread_config.card_count
```

**장점**:
- 새로운 스프레드 타입도 병렬 처리 지원 가능
- 코드 수정 없이 설정만 추가하면 동작

### 3. 중복 코드 제거

**제거된 중복**:
- `card_count_map` → `get_card_count()` 함수 사용
- `template_map` → `get_prompt_template_path()` 함수 사용
- `position_names` 딕셔너리 → `get_position_names()` 함수 사용
- `MAX_TOKENS_CONFIG` → `get_max_tokens()` 함수 사용

**적용 위치**:
- `readings_stream.py`: SSE 스트리밍 엔드포인트
- `readings.py`: 일반 리딩 엔드포인트
- `parallel_reading_engine.py`: 병렬 처리 엔진

## 새로운 스프레드 타입 추가 방법

### 예시: 호로스코프 리딩 추가

```python
# backend/src/ai/prompt_engine/spread_config.py에 추가

"horoscope": SpreadConfig(
    spread_type="horoscope",
    card_count=12,  # 12개 별자리
    positions=[
        PositionInfo(index=0, position="aries", name="양자리", meaning="..."),
        PositionInfo(index=1, position="taurus", name="황소자리", meaning="..."),
        # ... 나머지 별자리
    ],
    supports_parallel=True,  # 병렬 처리 지원
    batch_size=4,  # 12장을 3개 배치로 (4장씩)
    parallel_templates={
        "card": "reading/horoscope_card.txt",
        "overall": "reading/horoscope_overall.txt",
        "relationships": "reading/horoscope_relationships.txt",
        "advice": "reading/horoscope_advice.txt",
    },
    max_tokens=4096
)
```

**필요한 작업**:
1. `SPREAD_CONFIGS`에 설정 추가 (위 예시)
2. 프롬프트 템플릿 파일 생성:
   - `backend/prompts/reading/horoscope_card.txt`
   - `backend/prompts/reading/horoscope_card_en.txt`
   - `backend/prompts/reading/horoscope_overall.txt`
   - `backend/prompts/reading/horoscope_overall_en.txt`
   - 등등...
3. (선택) 스키마에 스프레드 타입 추가 (`ReadingRequest.spread_type` 패턴)

**코드 수정 불필요**:
- `readings_stream.py`: 자동으로 병렬 엔진 사용
- `readings.py`: 자동으로 설정 기반 처리
- `parallel_reading_engine.py`: 설정 기반으로 동작

## 제공되는 유틸리티 함수

### `get_spread_config(spread_type: str) -> Optional[SpreadConfig]`
스프레드 타입에 맞는 전체 설정 반환

### `get_card_count(spread_type: str) -> int`
스프레드 타입에 맞는 카드 수 반환

### `get_position_names(spread_type: str) -> List[str]`
스프레드 타입에 맞는 포지션 이름 리스트 반환 (한글)

### `supports_parallel_processing(spread_type: str) -> bool`
스프레드 타입이 병렬 처리를 지원하는지 확인

### `get_prompt_template_path(spread_type: str, template_key: str, language: str) -> Optional[str]`
스프레드 타입에 맞는 프롬프트 템플릿 경로 반환

### `get_max_tokens(spread_type: str, language: str) -> int`
스프레드 타입에 맞는 최대 토큰 수 반환

### `register_spread_config(config: SpreadConfig)`
런타임에 새로운 스프레드 설정 등록 (동적 확장)

## 확장성 보장 사항

1. **설정 기반 동작**: 모든 스프레드별 차이점이 설정으로 관리됨
2. **코드 중복 제거**: 공통 로직은 함수로 추상화
3. **병렬 처리 지원**: `supports_parallel=True` 설정만으로 자동 활성화
4. **프롬프트 템플릿 관리**: 템플릿 경로도 설정으로 관리
5. **언어 지원**: 영어/한국어 프롬프트 자동 선택

## 검증 완료

- ✅ 켈틱 크로스 리딩 정상 동작 확인
- ✅ 기존 스프레드 타입(one_card, three_card) 정상 동작 확인
- ✅ 병렬 처리 자동 선택 로직 검증
- ✅ 프롬프트 템플릿 경로 동적 로드 검증
- ✅ 린터 오류 없음

## 향후 확장 예시

호로스코프 리딩 추가 시:
1. `spread_config.py`에 설정 1개 추가
2. 프롬프트 템플릿 파일 생성
3. 완료! (코드 수정 불필요)

```python
"horoscope": SpreadConfig(
    spread_type="horoscope",
    card_count=12,
    positions=[...],
    supports_parallel=True,
    batch_size=4,
    max_concurrent_calls=6,  # 동시 호출 수 제한
    parallel_templates={
        "card": "reading/horoscope_card.txt",
        "overall": "reading/horoscope_overall.txt",
    },
    max_tokens=4096
)
```

## 병렬 처리 LLM 관리

### 동시 호출 수 제한

각 스프레드는 `max_concurrent_calls` 필드로 동시 LLM 호출 수를 제한할 수 있습니다:

- **켈틱 크로스**: 5개 동시 호출
- **호로스코프**: 6개 동시 호출 (더 많은 카드)
- **기본값**: 5개 (설정하지 않은 경우)

이 제한은 `asyncio.Semaphore`를 통해 구현되어 Rate Limiting을 보장합니다.

### LLM 할당 전략

작업 유형별로 최적의 모델이 자동 할당됩니다:

- **카드 해석**: 빠르고 저렴한 모델 (`claude-haiku`)
- **종합 리딩**: 고성능 모델 (`claude-sonnet`)
- **관계 분석**: 중간 성능 모델
- **조언**: 중간 성능 모델

자세한 내용은 `docs/LLM_MANAGEMENT.md`를 참조하세요.

