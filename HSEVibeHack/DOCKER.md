# Запуск VibeHack в Docker

## 📋 Требования

- **Docker** (версия 20.10+)
- **Docker Compose** (версия 1.29+)
- ~4GB памяти для Ollama при первом запуске
- ~20GB свободного места (для модели Qwen2)

## 🚀 Быстрый старт

### 1. Подготовка

```bash
cd ~/Desktop/VibeHack

# Убедитесь, что .env файл существует
cat .env

# Если нужно - отредактируйте переменные окружения
# DATABASE_URL, REDIS_URL, OLLAMA_BASE_URL и т.д.
```

### 2. Запуск всех сервисов

```bash
# Построить и запустить все контейнеры
docker-compose up --build

# Или в фоне
docker-compose up -d --build
```

### 3. Доступ к приложению

После запуска все сервисы будут доступны:

| Сервис | URL | Описание |
|--------|-----|---------|
| **Frontend** | http://localhost:3000 | UI приложения |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger документация |
| **PostgreSQL** | localhost:5432 | База данных |
| **Redis** | localhost:6379 | Кэш |
| **Ollama** | http://localhost:11434 | LLM сервис |

## 📊 Сервисы в Docker Compose

```
vibehack-api       (Port 8000) - FastAPI бэкенд
vibehack-frontend  (Port 3000) - HTTP сервер фронтенда
postgres           (Port 5432) - База данных
redis              (Port 6379) - Redis кэш
ollama             (Port 11434) - AI модель Qwen2
```

## ⚙️ Часто используемые команды

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f vibehack-api
docker-compose logs -f vibehack-frontend
docker-compose logs -f postgres
docker-compose logs -f ollama

# Последние 100 строк
docker-compose logs -f --tail=100
```

### Остановка и удаление

```bash
# Остановить контейнеры
docker-compose stop

# Остановить и удалить контейнеры
docker-compose down

# Удалить всё включая том (ВНИМАНИЕ - удалит БД!)
docker-compose down -v
```

### Перезагрузка сервиса

```bash
# Перезагрузить API
docker-compose restart vibehack-api

# Перезагрузить фронтенд
docker-compose restart vibehack-frontend
```

### Запуск команд в контейнере

```bash
#執行bash в контейнере API
docker-compose exec vibehack-api bash

# Проверить статус БД
docker-compose exec postgres pg_isready -U vibehack -d vibehack

# Проверить Redis
docker-compose exec redis redis-cli ping
```

## 🧪 Тестирование в Docker

### 1. Проверить здоровье API

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{"status": "healthy"}
```

### 2. Запустить парсеры

```bash
curl -X POST http://localhost:8000/hackathons/parse/update
```

### 3. Получить список хакатонов

```bash
curl http://localhost:8000/hackathons?limit=5
```

### 4. Проверить логи

```bash
# API логи
docker-compose logs vibehack-api | tail -20

# Все ошибки
docker-compose logs | grep ERROR
```

## 🔧 Переменные окружения

Создайте `.env` файл (уже должен существовать):

```env
# Database
DATABASE_URL=postgresql://vibehack:vibehack_pass@postgres:5432/vibehack
REDIS_URL=redis://redis:6379/0

# Frontend
FRONTEND_URL=http://localhost:3000

# Ollama
OLLAMA_BASE_URL=http://ollama:11434

# JWT
JWT_SECRET=vibehack

# Google OAuth (опционально)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

## 📁 Структура томов

```
postgres_data/     → База данных PostgreSQL
redis_data/        → Redis persistence
ollama_data/       → Модели Ollama (20GB+)
```

**Внимание**: Если удалить томы (`docker-compose down -v`), потеряются все данные!

## 🐛 Проблемы и решения

### Порт уже занят

```bash
# Найти процесс на порту
lsof -i :8000    # API
lsof -i :3000    # Frontend
lsof -i :5432    # PostgreSQL

# Убить процесс (если нужно)
kill -9 <PID>
```

### PostgreSQL не запускается

```bash
# Проверить логи
docker-compose logs postgres

# Удалить том БД и пересоздать
docker-compose down -v postgres
docker-compose up -d postgres
```

### Ollama медленно загружается

Первая загрузка Ollama может занять 5-10 минут (скачивание модели Qwen2).

```bash
# Проверить статус
docker-compose logs ollama | tail -50

# Дождитесь сообщения типа "Model loaded"
```

### API не подключается к БД

```bash
# Проверить соединение
docker-compose exec vibehack-api python -c \
  "from backend.database import SessionLocal; print(SessionLocal())"

# Посмотреть логи
docker-compose logs vibehack-api
```

## 🚀 Production развёртывание

Для production используйте:

```bash
# Без режима разработки (reload)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Или отредактируйте команду в docker-compose.yml:
# command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 📊 Мониторинг

Проверить статус контейнеров:

```bash
docker-compose ps

# Вывод покажет:
# NAME                   STATUS
# vibehack-api           Up (healthy)
# vibehack-frontend      Up
# vibehack-postgres      Up (healthy)
# vibehack-redis         Up (healthy)
# vibehack-ollama        Up
```

## 🔐 Безопасность

**⚠️ Для development только!**

Для production:
1. Измените пароли БД в `.env`
2. Используйте реальный `JWT_SECRET`
3. Настройте SSL/TLS
4. Ограничьте доступ с помощью firewall
5. Используйте Nginx reverse proxy

## 📚 Дополнительно

### Как добавить новый сервис

Отредактируйте `docker-compose.yml`:

```yaml
services:
  my-service:
    image: my-image:latest
    ports:
      - "9000:9000"
    networks:
      - vibehack-network
```

### Как сохранить изменения

База данных автоматически сохраняется в `postgres_data/`.
Для бэкапа:

```bash
# Экспортировать БД
docker-compose exec postgres pg_dump -U vibehack vibehack > backup.sql

# Импортировать БД
docker-compose exec -T postgres psql -U vibehack vibehack < backup.sql
```

## 💡 Советы

- Используйте `docker-compose logs -f` для отладки
- Запускайте парсеры с помощью API endpoint
- Проверяйте `logs/` директорию в хост машине
- При изменениях в коде пересоберите с `--build`

---

**Готово! 🎉** Приложение полностью работает в Docker контейнерах.
