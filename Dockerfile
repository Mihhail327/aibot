# Stage 1: Builder
FROM python:3.13-slim AS builder

# Устанавливаем poetry
RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Конфигурируем Poetry для создания виртуального окружения (.venv) внутри рабочей директории
# Устанавливаем зависимости напрямую, игнорируя баги poetry-plugin-export
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-interaction --no-ansi

# Stage 2: Runtime
FROM python:3.13-slim

# Создаем непривилегированного пользователя для безопасности (Security)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Копируем готовое виртуальное окружение из builder-стейджа
COPY --from=builder /app/.venv /app/.venv

# Копируем исходный код приложения и конфигурации миграций
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic

# Меняем права доступа для безопасного запуска
RUN chown -R appuser:appgroup /app
USER appuser

# Добавляем бинарники виртуального окружения в начало PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]