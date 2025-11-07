import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy
import sqlalchemy.orm as sa_orm

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")


def _fake_engine(*_args, **_kwargs):
    return SimpleNamespace()


def _fake_sessionmaker(*_args, **_kwargs):
    def _session():
        return SimpleNamespace(close=lambda: None)

    return _session


sqlalchemy.create_engine = _fake_engine
sa_orm.sessionmaker = _fake_sessionmaker

sys.modules.setdefault(
    "email_validator",
    SimpleNamespace(
        validate_email=lambda email, *_args, **_kwargs: SimpleNamespace(email=email),
        EmailNotValidError=Exception,
    )
)


class _PsycopgStub:
    paramstyle = "pyformat"
    extras = SimpleNamespace()

    def connect(self, *args, **kwargs):
        return None


sys.modules.setdefault("psycopg2", _PsycopgStub())


class _RedisClient(SimpleNamespace):
    def ping(self):
        return True


def _redis_from_url(*_args, **_kwargs):
    return _RedisClient()


sys.modules.setdefault("redis", SimpleNamespace(from_url=_redis_from_url, Redis=SimpleNamespace))


class _FakeAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, **kwargs):
        usage = SimpleNamespace(input_tokens=0, output_tokens=0)
        return SimpleNamespace(content=[SimpleNamespace(text="stub")], model="stub", usage=usage, stop_reason="stop")

    async def close(self):
        return None


sys.modules.setdefault(
    "anthropic",
    SimpleNamespace(
        AsyncAnthropic=_FakeAnthropic,
        APIError=Exception,
        RateLimitError=Exception,
        AuthenticationError=Exception,
        APITimeoutError=Exception,
    ),
)


class _SentenceTransformerStub:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, *args, **kwargs):
        return [[0.0, 0.0, 0.0] for _ in texts]

    def encode_single(self, _text):
        return [0.0, 0.0, 0.0]

    def get_sentence_embedding_dimension(self):
        return 3


sys.modules.setdefault(
    "sentence_transformers",
    SimpleNamespace(SentenceTransformer=_SentenceTransformerStub),
)

sys.modules.setdefault(
    "jwt",
    SimpleNamespace(
        encode=lambda *args, **kwargs: "token",
        decode=lambda *args, **kwargs: {},
        PyJWTError=Exception,
    ),
)

module_path = Path(__file__).resolve().parents[1] / "src" / "api" / "routes" / "readings_stream.py"
spec = importlib.util.spec_from_file_location("src.api.routes.readings_stream", module_path)
readings_stream = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = readings_stream
spec.loader.exec_module(readings_stream)
from src.core.card_shuffle import CardData, DrawnCard, Orientation
from src.schemas.reading import ReadingRequest
from src.ai.models import AIResponse, OrchestratorResponse


class FakeAdvice(SimpleNamespace):
    def model_dump(self):
        return dict(self.__dict__)


class FakeDBProvider:
    def __init__(self) -> None:
        self.saved_data = None
        self.persisted = asyncio.Event()

    async def create_reading(self, reading_data):
        self.saved_data = reading_data
        self.persisted.set()

        class StubReading:
            def __init__(self, reading_id: str) -> None:
                self.id = reading_id

        return StubReading(reading_data["id"])


@pytest.mark.asyncio
async def test_generate_reading_stream_schedules_background_persistence(monkeypatch):
    readings_stream._persistence_tasks.clear()

    card = CardData(
        id=1,
        name="The Fool",
        name_ko="바보",
        arcana_type="major",
        number=0,
        suit=None,
        keywords_upright=["start"],
        keywords_reversed=["risk"],
        meaning_upright="새로운 시작",
        meaning_reversed="주의",
        description=None,
        symbolism=None,
        image_url=None,
    )
    drawn_card = DrawnCard(card, Orientation.UPRIGHT)

    async def fake_draw_cards(*args, **kwargs):
        return [drawn_card]

    monkeypatch.setattr(readings_stream.CardShuffleService, "draw_cards", fake_draw_cards)
    monkeypatch.setattr(
        readings_stream.ContextBuilder,
        "build_card_context",
        staticmethod(lambda _: {"id": card.id, "name": card.name})
    )

    class FakeEnricher:
        async def enrich_prompt_context_async(self, **kwargs):
            return {"card_contexts": [], "spread_context": {}, "category_guidance": None}

    monkeypatch.setattr(readings_stream, "get_context_enricher", lambda: FakeEnricher())

    class FakeTemplate:
        def __init__(self, text: str) -> None:
            self._text = text

        def render(self, **kwargs):
            return self._text

    class FakeJinja:
        def get_template(self, name: str):
            if name.startswith("system"):
                return FakeTemplate("system")
            if name.startswith("output"):
                return FakeTemplate("{\"summary\": \"stub\"}")
            return FakeTemplate("prompt")

    monkeypatch.setattr(readings_stream, "jinja_env", FakeJinja())

    fake_ai_response = AIResponse(
        content="stub",
        model="stub",
        provider="stub",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        finish_reason="stop",
    )

    class FakeOrchestrator:
        async def generate(self, **kwargs):
            return OrchestratorResponse(
                response=fake_ai_response,
                all_attempts=[fake_ai_response],
                total_cost=0.0,
            )

    monkeypatch.setattr(readings_stream, "get_orchestrator", lambda: FakeOrchestrator())

    class FakeParser:
        def parse(self, _content):
            return SimpleNamespace(
                summary="요약",
                cards=[SimpleNamespace(position="현재", interpretation="해석", key_message="핵심")],
                overall_reading="전체",
                advice=FakeAdvice(headline="조언"),
                card_relationships=None,
            )

    monkeypatch.setattr(readings_stream, "ResponseParser", lambda: FakeParser())
    monkeypatch.setattr(readings_stream, "ReadingValidator", lambda: SimpleNamespace(validate_reading_quality=lambda *args, **kwargs: None))

    db_provider = FakeDBProvider()

    request = ReadingRequest(question="새로운 시작?", spread_type="one_card", category="career")

    events = []
    async for event in readings_stream.generate_reading_stream(request, "user-1", db_provider):
        events.append(event)

    assert any("저장 백그라운드 처리 중" in event for event in events)
    complete_event = next(evt for evt in events if "event: complete" in evt)
    payload_line = next(line for line in complete_event.split("\n") if line.startswith("data:"))
    payload = json.loads(payload_line.replace("data:", "").strip())
    reading_id = payload["reading_id"]

    await asyncio.wait_for(db_provider.persisted.wait(), timeout=0.5)
    assert db_provider.saved_data is not None
    assert db_provider.saved_data["id"] == reading_id

    readings_stream._persistence_tasks.clear()
