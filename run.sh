#!/bin/bash
# Удобный скрипт запуска бота

set -e

echo "🤖 Google Calendar Telegram Bot"
echo "================================"
echo ""

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python -m venv venv
    echo "✅ Виртуальное окружение создано"
fi

# Активация виртуального окружения
source venv/bin/activate

# Проверка зависимостей
echo "📚 Проверяю зависимости..."
pip install -q -r requirements.txt

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "   Копирую из .env_example..."
    cp .env_example .env
    echo ""
    echo "❗ ВАЖНО: Отредактируйте .env и добавьте TELEGRAM_BOT_TOKEN"
    echo "   После этого запустите скрипт снова"
    exit 1
fi

# Проверка credentials
if [ ! -f "credentials/google_credentials.json" ]; then
    echo "⚠️  Файл credentials/google_credentials.json не найден!"
    echo ""
    echo "Инструкция:"
    echo "1. Получите credentials в Google Cloud Console"
    echo "2. Сохраните файл как credentials/google_credentials.json"
    echo "3. Запустите скрипт снова"
    echo ""
    echo "Подробнее: см. INSTALLATION.md"
    exit 1
fi

# Установка браузера по умолчанию (для OAuth)
if command -v chromium &> /dev/null; then
    export BROWSER=$(which chromium)
    echo "🌐 Браузер: Chromium"
elif command -v google-chrome &> /dev/null; then
    export BROWSER=$(which google-chrome)
    echo "🌐 Браузер: Chrome"
elif command -v firefox &> /dev/null; then
    export BROWSER=$(which firefox)
    echo "🌐 Браузер: Firefox"
else
    echo "⚠️  Браузер не найден, OAuth может не работать"
fi

# Установка пути к Google OAuth credentials для MCP сервера
export GOOGLE_OAUTH_CREDENTIALS="$(pwd)/credentials/google_credentials.json"
echo "🔑 OAuth credentials: $GOOGLE_OAUTH_CREDENTIALS"

echo ""
echo "🚀 Запускаю бота..."
echo "   (Нажмите Ctrl+C для остановки)"
echo ""

# Запуск бота
python main.py
