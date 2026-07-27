# AI Bot — Автоматический сбор и публикация новостей в Telegram

Автоматизированный сервис на **Python 3.13 / FastAPI / Celery / Telethon / Aiogram 3 / OpenAI** для парсинга новостей из Telegram-каналов и RSS-лент, фильтрации по ключевым словам, AI-обработки и публикации постов в ваш Telegram-канал с поддержкой медиафайлов (картинок).

---

## 🚀 Возможности системы

- **Парсинг Telegram-каналов**: Сбор постов в реальном времени через Telegram MTProto (Telethon).
- **Парсинг RSS-лент**: Автоматический сбор новостей из RSS/Atom источников.
- **Фильтрация по ключевым словам**: Сохранение и обработка только тех постов, которые соответствуют заданным ключевым словам.
- **AI-генерация постов**: Форматирование и рерайт текста с помощью OpenAI (`gpt-4o-mini`) с добавлением emoji и Call to Action.
- **Поддержка медиафайлов**: Автоматическое скачивание изображений из оригинальных постов и их публикация вместе с текстом.
- **Красивый HTML-фоллбэк**: Если квота OpenAI исчерпана, система автоматически преобразует оригинальный пост в аккуратный Telegram HTML с кликабельными ссылками.
- **Фоновые задачи и расписание**: Планировщик Celery Beat запускает сборы каждые 30 минут.
- **Полное ручное управление через REST API**:
  - Ручной запуск парсинга всех источников или конкретного источника (`POST /api/v1/sources/parse`, `POST /api/v1/sources/{source_id}/parse`).
  - Ручная генерация поста для конкретной новости с сохранением в пайплайн БД (`POST /api/v1/posts/generate/{news_id}`).
  - Ручная публикация любого сгенерированного поста в Telegram (`POST /api/v1/posts/{post_id}/publish`).
  - Просмотр логов ошибок задач и постов (`GET /api/v1/logs/errors`).
- **Защищенная авторизация админки**: Установка мастер-пароля (`POST /api/v1/auth/setup`) требует валидный `invite_token`. Защита логина при неинициализированной базе.
- **Устойчивость к сбоям (Resiliency)**: Повторные попытки вызова OpenAI и Telegram API с экспоненциальной задержкой (`tenacity`).
- **Защита от спама (Rate Limiting)**: Ограничение частоты запросов к эндпоинтам авторизации и управления (`slowapi`).

---

## 🛠 Технологический стек

- **Язык**: Python 3.13
- **Веб-фреймворк**: FastAPI + Uvicorn
- **База данных**: PostgreSQL 15 + SQLAlchemy 2.0 (Async) + Alembic (миграции)
- **Очереди задач и кэш**: Celery 5.6 + Redis 7
- **Парсинг Telegram**: Telethon (MTProto API)
- **Публикация в Telegram**: Aiogram 3 (Bot API)
- **ИИ / Генерация**: OpenAI API (`gpt-4o-mini`)
- **Устойчивость и Защита**: Tenacity (Retry) + SlowAPI (Rate Limiter)
- **Мониторинг**: Flower (Celery Web UI с поддержкой Basic Auth)
- **Контейнеризация**: Docker & Docker Compose (Dev / Prod)

---

## 📁 Структура проекта

```text
aibot/
├── alembic/                # Миграции структуры базы данных
│   └── versions/           # Файлы миграций Alembic
├── app/                    # Исходный код приложения
│   ├── api/                # REST API эндпоинты (v1)
│   ├── core/               # Конфигурации, БД, Celery, безопасность, limiter
│   ├── domains/            # Доменная логика (DDD)
│   │   ├── auth/           # Защищенная авторизация и токены
│   │   ├── keywords/       # Управление ключевыми словами
│   │   ├── logs/           # Просмотр логов ошибок
│   │   ├── news/           # Сбор и хранение новостей
│   │   ├── posts/          # Генерация и статус публикаций
│   │   └── sources/        # Управление источниками (Telegram / RSS)
│   └── infrastructure/     # Внешние сервисы (tenacity retry)
│       ├── ai/             # Клиент OpenAI и генераторы
│       ├── parsers/        # Парсеры Telegram и RSS
│       └── telegram/       # MTProto клиент и Бот-публикатор Aiogram
├── media/                  # Хранилище скачанных изображений (монтируется в Docker)
├── .env.example            # Пример файла конфигурации и переменных окружения
├── docker-compose.yml      # Docker Compose конфигурация для разработки (Dev)
├── docker-compose.prod.yml # Docker Compose конфигурация для продакшена (Prod)
├── Dockerfile              # Сборка приложения (Multi-stage)
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

### Режим разработки (Development)

```bash
docker compose up -d --build
```

### Продакшн режим (Production)

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Применение миграций базы данных

```bash
docker compose exec api alembic upgrade head
```

---

## 🌐 Веб-интерфейсы

* **Swagger UI (REST API)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Flower (Мониторинг Celery)**: [http://localhost:5555](http://localhost:5555)

---

## 🛠 Полезные команды управления

### Запустить парсинг новостей вручную через API:

```bash
curl -X POST http://localhost:8000/api/v1/sources/parse
```

### Просмотр логов ошибок постов:

```bash
curl -X GET http://localhost:8000/api/v1/logs/errors
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

## 📝 Лицензия

Проект распространяется под лицензией MIT.