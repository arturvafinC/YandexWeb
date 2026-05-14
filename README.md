# Музей ошибок

«Музей ошибок» — учебный Flask WEB-проект для хранения, анализа и повторения учебных ошибок. Пользователь регистрируется, добавляет ошибки по предметам и темам, фиксирует неправильный и правильный ответ, объяснение, статус, дату повторения и изображение задания.

## Проблема

При подготовке к экзаменам ошибки часто исправляются один раз и забываются. Проект помогает собирать причины ошибок, видеть слабые темы и планировать повторение.

## Основные функции

- Регистрация, вход, выход и защита личных страниц через Flask-Login.
- CRUD ошибок с предметами, типами ошибок, тегами, статусами и изображениями.
- Фильтры по предмету, статусу и типу ошибки.
- Раздел «Повторить сегодня» по статусу или дате `repeat_at`.
- Статистика по статусам, предметам, типам и проценту исправленных ошибок.
- REST API `/api/mistakes` для ошибок текущего пользователя.
- CSRF для HTML-форм, JSON-ответы API, кастомные страницы 403/404/500.
- Логирование действий в `logs/app.log`.

## Стек

Python, Flask, Jinja2, Bootstrap, HTML, CSS, Flask-WTF, WTForms, Flask-Login, SQLite, SQLAlchemy ORM, Alembic, REST API, JSON, logging, requests.

## Структура проекта

```text
app/
  auth/ main/ mistakes/ api/
  templates/
  static/css/
  static/uploads/
migrations/
scripts/
logs/
run.py
requirements.txt
README.md
TEST_CASES.md
TEST_REPORT.md
```

## Запуск

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_data.py
python run.py
```

Адрес: `http://127.0.0.1:5000`. Для деплоя приложение слушает `0.0.0.0`, порт берётся из `PORT` или по умолчанию `5000`.

## Быстрый старт

```bash
chmod +x start.sh
./start.sh
```

## Миграции

```bash
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```

В проекте уже есть первая миграция `migrations/versions/0001_initial.py`.

## Стартовые данные

```bash
python scripts/seed_data.py
```

Скрипт безопасен для повторного запуска и добавляет предметы, типы ошибок и теги без дублей.

## API

Все API-эндпоинты требуют авторизации cookie-сессией.

- `GET /api/mistakes` — список ошибок текущего пользователя.
- `GET /api/mistakes/<id>` — одна ошибка.
- `POST /api/mistakes` — создать ошибку.
- `PUT /api/mistakes/<id>` — полностью обновить ошибку.
- `PATCH /api/mistakes/<id>` — частично обновить ошибку.
- `DELETE /api/mistakes/<id>` — удалить ошибку.

Пример JSON:

```json
{
  "title": "Ошибка в квадратном уравнении",
  "subject": "Математика",
  "topic": "Квадратные уравнения",
  "mistake_type": "Ошибка в формуле",
  "status": "Нужно повторить",
  "wrong_answer": "x = 3",
  "correct_answer": "x = -3",
  "explanation": "Ошибка при раскрытии скобок",
  "tags": ["ЕГЭ"]
}
```

## Smoke-test

При запущенном сервере:

```bash
python scripts/smoke_test.py http://127.0.0.1:5000
```

Smoke-test проверяет главную страницу, регистрацию, вход, dashboard, создание ошибки через API, получение списка и детали, PATCH статуса, DELETE и запрет API без авторизации.

## Что проверено

Итоговые результаты проверки фиксируются в `TEST_REPORT.md`.

## Возможные улучшения

- Пагинация списка ошибок.
- Поиск по тексту.
- Удаление старых загруженных изображений при замене.
- Экспорт ошибок в CSV/JSON.
- Более подробная визуальная аналитика.
