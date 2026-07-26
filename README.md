
```
# AI Bot — Автоматический сбор и публикация новостей в Telegram

Автоматизированный сервис на Python/FastAPI/Celery для парсинга новостей из Telegram-каналов и RSS-лент, фильтрации по ключевым словам, AI-обработки (OpenAI) и публикации постов в ваш Telegram-канал с медиафайлами (картинками).

---

## 🚀 Возможности системы

- **Парсинг Telegram-каналов**: Сбор постов в реальном времени через Telegram MTProto (Telethon).
- **Парсинг RSS-лент**: Автоматический сбор новостей из RSS/Atom источников.
- **Фильтрация по ключевым словам**: Сохранение и обработка только тех постов, которые соответствуют заданным ключевым словам.
- **AI-генерация постов**: Форматирование и рерайт текста с помощью OpenAI (`gpt-4o-mini`) с добавлением emoji и Call to Action.
- **Поддержка медиафайлов**: Автоматическое скачивание изображений из оригинальных постов и их публикация вместе с текстом.
- **Красивый HTML-фоллбэк**: Если квота OpenAI исчерпана, система автоматически преобразует оригинальный пост в аккуратный Telegram HTML с кликабельными ссылками.
- **Фоновые задачи и расписание**: Планировщик Celery Beat запускает сборы каждые 30 минут.
- **REST API и веб-интерфейс**: Управление источниками, ключевыми словами и постом через FastAPI и Swagger UI.

---

## 🛠 Технологический стек

- **Язык**: Python 3.13
- **Веб-фреймворк**: FastAPI + Uvicorn
- **База данных**: PostgreSQL 15 + SQLAlchemy 2.0 (Async) + Alembic (миграции)
- **Очереди задач и кэш**: Celery 5.6 + Redis 7
- **Парсинг Telegram**: Telethon (MTProto API)
- **Публикация в Telegram**: Aiogram 3 (Bot API)
- **ИИ / Генерация**: OpenAI API (`gpt-4o-mini`)
- **Мониторинг**: Flower (Celery Web UI)
- **Контейнеризация**: Docker & Docker Compose

---

## 📁 Структура проекта

```text
aibot/
├── alembic/                # Миграции структуры базы данных
│   └── versions/           # Файлы миграций Alembic
├── app/                    # Исходный код приложения
│   ├── api/                # REST API эндпоинты (v1)
│   ├── core/               # Конфигурации, БД, Celery app, безопасность
│   ├── domains/            # Доменная логика (DDD)
│   │   ├── auth/           # Авторизация и токены
│   │   ├── keywords/       # Управление ключевыми словами
│   │   ├── news/           # Сбор и хранение новостей
│   │   ├── posts/          # Генерация и статус публикаций
│   │   └── sources/        # Управление источниками (Telegram / RSS)
│   └── infrastructure/     # Внешние сервисы
│       ├── ai/             # Клиент OpenAI и генераторы
│       ├── parsers/        # Парсеры Telegram и RSS
│       └── telegram/       # MTProto клиент и Бот-публикатор Aiogram
├── media/                  # Хранилище скачанных изображений (монтируется в Docker)
├── .env.example            # Пример файла конфигурации и переменных окружения
├── docker-compose.yml      # Docker Compose конфигурация сервисов
├── Dockerfile              # Сборка приложения
├── pyproject.toml          # Зависимости проекта (Poetry)
└── README.md               # Документация проекта

```

---

## ⚙️ Настройка конфигурации (.env)

Перед запуском скопируйте `.env.example` в `.env` и укажите ваши реальные учетные данные:

```bash
cp .env.example .env

```

> ⚠️ **Важно**: Добавьте вашего бота (`TELEGRAM_BOT_TOKEN`) в ваш Telegram-канал в качестве **Администратора** с разрешением *"Публикация сообщений"* (Post Messages).

---

## 🚀 Быстрый запуск

### 1. Сборка и запуск контейнеров

```bash
docker compose up -d --build

```

### 2. Применение миграций базы данных

*(Миграции также могут применяться автоматически при старте API-сервиса)*

```bash
docker compose exec api alembic upgrade head

```

---

## 🌐 Веб-интерфейсы

* **Swagger UI (REST API)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Flower (Мониторинг Celery)**: [http://localhost:5555](http://localhost:5555)

---

## 🛠 Полезные команды управления

### Запустить парсинг новостей вручную:

```bash
docker compose exec api python -c "from app.core.celery_app import celery_app; from app.domains.news.tasks import parse_channels_task; parse_channels_task.delay()"

```

### Просмотр логов воркера в реальном времени:

```bash
docker compose logs -f celery_worker

```

### Перезапуск воркера и мониторинга:

```bash
docker compose restart celery_worker flower

```

### Остановка всех сервисов:

```bash
docker compose down

```

---
### 📝 Лицензия
Проект распространяется под лицензией MIT.

```