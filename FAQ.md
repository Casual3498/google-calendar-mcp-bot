# ❓ Частые вопросы (FAQ)

## Общие вопросы

### Что такое MCP?

**MCP (Model Context Protocol)** - это протокол для взаимодействия с внешними сервисами. Мы используем MCP сервер `@cocal/google-calendar-mcp` для работы с Google Calendar.

### Почему для задач используется прямой API, а для событий MCP?

- **События** - через MCP для поддержки естественного языка
- **Задачи** - через прямой API для явных команд

Это позволяет использовать сильные стороны каждого подхода.

### В чем разница между событиями и задачами?

| Событие | Задача |
|---------|--------|
| Имеет время начала и конца | Имеет только дату |
| Может повторяться | Не повторяется |
| Создается естественным языком | Создается командой |
| Хранится в Google Calendar | Хранится в Google Tasks |

## Проблемы с установкой

### `npm: command not found`

Установите Node.js:

```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# Manjaro/Arch
sudo pacman -S nodejs npm

# macOS
brew install node
```

### `ModuleNotFoundError: No module named 'aiogram'`

Активируйте виртуальное окружение:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### `Failed to start server: Error loading OAuth keys`

Проверьте путь к credentials:

```bash
export GOOGLE_OAUTH_CREDENTIALS="$(pwd)/credentials/google_credentials.json"
```

## Проблемы с авторизацией

### `Error 403: access_denied`

Добавьте свой email в **Test users**:
1. [Google Cloud Console](https://console.cloud.google.com)
2. **OAuth consent screen**
3. **Test users** → **Add users**
4. Добавьте свой email

### `Authentication tokens are no longer valid`

Переавторизуйтесь:

```bash
# Calendar
npx @cocal/google-calendar-mcp auth

# Tasks
python reauth_tasks_only.py
```

### `Request had insufficient authentication scopes`

Нужны дополнительные разрешения:

```bash
# Для полного доступа к задачам
python reauth_tasks_only.py
```

## Проблемы с работой бота

### Бот не отвечает

1. Проверьте, запущен ли бот:
```bash
ps aux | grep "python main.py"
```

2. Проверьте логи:
```bash
tail -f /tmp/bot_*.log
```

3. Перезапустите:
```bash
pkill -f "python main.py"
./run.sh
```

### `TelegramConflictError: terminated by other getUpdates request`

Запущено несколько экземпляров бота. Остановите все:

```bash
pkill -f "python main.py"
docker compose down
./run.sh
```

### Бот не находит события

**MCP серверу нужно время для синхронизации.** Подождите 5-10 секунд и повторите запрос.

### Бот не понимает команду

Проверьте формат:

✅ **Правильно:**
```
Создай событие "встреча" на завтра в 10:00
/create_task Купить молоко | завтра
```

❌ **Неправильно:**
```
Создай задачу "встреча" на завтра в 10:00  # Для задач используйте /create_task
/create_event Встреча  # Для событий используйте естественный язык
```

## Проблемы с датами и временем

### Задача создается на неправильную дату

Google Tasks API имеет особенности работы с таймзонами. Убедитесь, что:
1. Используете формат: `/create_task Название | дата`
2. Дата указана правильно: `завтра`, `20.01`, `понедельник`

### "Позавчера" показывает "Вчера"

Это было исправлено в последней версии. Обновите код:

```bash
git pull
pkill -f "python main.py"
./run.sh
```

### Время задачи всегда 00:00

**Это нормально!** Google Tasks API не поддерживает время, только дату.

Для событий со временем используйте календарь:
```
Создай встречу на завтра в 10:00
```

## Проблемы с повторяющимися событиями

### Бот не показывает повторяющиеся события

Убедитесь, что в коде используется `singleEvents: True`:

```python
# bot/mcp_client.py
arguments = {
    'calendarId': 'primary',
    'timeMin': start_date,
    'timeMax': end_date,
    'maxResults': max_results,
    'singleEvents': True  # ← Важно!
}
```

### Как создать повторяющееся событие?

Создайте через веб-интерфейс Google Calendar:
1. Откройте [Google Calendar](https://calendar.google.com)
2. Создайте событие
3. Выберите "Повторяется"
4. Настройте расписание

Бот автоматически увидит все экземпляры.

## Docker

### `docker: command not found`

Установите Docker:

```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose

# Manjaro/Arch
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
```

### `permission denied while trying to connect to the Docker daemon`

Добавьте пользователя в группу docker:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Контейнер не запускается

Проверьте логи:

```bash
docker compose logs -f
```

## Тестирование

### Тесты не проходят

1. Убедитесь, что бот не запущен:
```bash
pkill -f "python main.py"
```

2. Проверьте авторизацию:
```bash
npx @cocal/google-calendar-mcp auth
python reauth_tasks_only.py
```

3. Запустите тесты:
```bash
./run_tests.sh
```

### "Found created event" - тест не проходит

Это известная проблема - MCP серверу нужно время для синхронизации. Не критично для реального использования.

## Производительность

### Бот медленно отвечает

1. **Первый запрос всегда медленнее** - идет подключение к API
2. **MCP серверу нужно время** - подождите 2-3 секунды
3. **Проверьте интернет** - все запросы идут через Google API

### `TelegramNetworkError: Request timeout error`

Увеличьте таймаут в коде или проверьте интернет-соединение.

## Безопасность

### Где хранятся токены?

```
~/.config/google-calendar-mcp/token.json  # Calendar (MCP)
~/.config/google-calendar-mcp/tasks_token.json  # Tasks (API)
```

### Как удалить все токены?

```bash
rm -rf ~/.config/google-calendar-mcp/
```

Затем переавторизуйтесь.

### Безопасно ли хранить credentials в проекте?

`credentials/` добавлена в `.gitignore`, файлы не попадут в git. Но для production используйте переменные окружения или секреты.

## Разработка

### Как добавить новую команду?

1. Создайте обработчик в `handlers/`
2. Зарегистрируйте в `bot/bot_instance.py`
3. Добавьте в `/help` в `handlers/common_handlers.py`

### Как изменить таймзону?

Отредактируйте `MOSCOW_TZ` в файлах:
- `handlers/calendar_handlers.py`
- `handlers/tasks_handlers.py`
- `bot/tasks_client.py`

### Как включить debug логи?

В `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Еще вопросы?

1. Проверьте [README.md](README.md)
2. Посмотрите [EXAMPLES.md](EXAMPLES.md)
3. Запустите тесты: `./run_tests.sh`
4. Проверьте логи: `tail -f /tmp/bot_*.log`
