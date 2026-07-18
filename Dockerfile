# Stage 1: Builder
FROM python:3.13-slim AS builder

# Устанавливаем poetry
RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Экспортируем зависимости в requirements.txt и устанавливаем их
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

# Создаем непривилегированного пользователя для безопасности (Security)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Копируем зависимости из первого стейджа
COPY --from=builder /root/.local /home/appuser/.local
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic

# Меняем права и переключаемся на пользователя
RUN chown -R appuser:appgroup /app
USER appuser

# Добавляем локальные бинарники в PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]