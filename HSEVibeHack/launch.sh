#!/bin/bash
# Скрипт для быстрого запуска VibeHack в Docker

set -e

echo "🚀 VibeHack Docker Launcher"
echo "================================"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "📥 Установите с https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "📥 Установите с https://docs.docker.com/compose/install"
    exit 1
fi

echo "✅ Docker найден: $(docker --version)"
echo "✅ Docker Compose найден: $(docker-compose --version)"
echo ""

# Меню
echo "Выберите действие:"
echo "1. 🚀 Запустить контейнеры"
echo "2. 🛑 Остановить контейнеры"
echo "3. 📊 Показать статус"
echo "4. 📋 Показать логи API"
echo "5. 🧹 Удалить контейнеры (сохранить данные)"
echo "6. 🗑️  Удалить всё (включая БД)"
echo "7. 🔄 Перезагрузить API"
echo "8. 📖 Открыть документацию"
echo ""

read -p "Выберите (1-8): " choice

case $choice in
    1)
        echo "🚀 Запуск контейнеров..."
        docker-compose up -d --build
        echo ""
        echo "✅ Контейнеры запущены!"
        echo ""
        echo "📍 Доступные сервисы:"
        echo "  • Frontend:   http://localhost:3000"
        echo "  • API:        http://localhost:8000"
        echo "  • Docs:       http://localhost:8000/docs"
        echo ""
        echo "Логи: docker-compose logs -f"
        ;;
    2)
        echo "🛑 Остановка контейнеров..."
        docker-compose stop
        echo "✅ Контейнеры остановлены"
        ;;
    3)
        echo "📊 Статус контейнеров:"
        echo ""
        docker-compose ps
        ;;
    4)
        echo "📋 Логи API (Ctrl+C для выхода):"
        echo ""
        docker-compose logs -f vibehack-api
        ;;
    5)
        echo "🧹 Удаление контейнеров (данные сохранены)..."
        docker-compose down
        echo "✅ Контейнеры удалены"
        ;;
    6)
        read -p "🗑️  ВНИМАНИЕ: Это удалит БД и все данные! Продолжить? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  Удаление всего..."
            docker-compose down -v
            echo "✅ Всё удалено"
        else
            echo "❌ Отменено"
        fi
        ;;
    7)
        echo "🔄 Перезагрузка API..."
        docker-compose restart vibehack-api
        echo "✅ API перезагружена"
        ;;
    8)
        echo "📖 Открытие документации..."
        if command -v xdg-open &> /dev/null; then
            xdg-open DOCKER.md
        elif command -v open &> /dev/null; then
            open DOCKER.md
        else
            echo "📄 Откройте файл DOCKER.md вручную"
        fi
        ;;
    *)
        echo "❌ Неправильный выбор"
        exit 1
        ;;
esac

echo ""
echo "✨ Готово!"
