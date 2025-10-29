FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정 (Cloud Run은 PORT 환경변수 사용)
ENV PORT=8080
EXPOSE 8080

# 기본 환경 변수 설정
ENV DEBUG=False
ENV DATABASE_PROVIDER=firestore

# 실행 명령 (Cloud Run의 PORT 환경변수 사용)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
