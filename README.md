# DataBase

Production-ready backend foundation for sprint 1 of the mountain pass submission project.

Подробное решение по спринту с анализом БД, архитектурными решениями и примерами находится в `docs/sprint_1_solution.md`.

## Технологический стек

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- `psycopg` v3

## Почему FastAPI + SQLAlchemy + psycopg

- `FastAPI` даёт строгую схему API, хорошую валидацию и удобный контракт JSON.
- `SQLAlchemy 2.0` даёт чистую ORM-модель, транзакционность и расширяемость.
- `psycopg` v3 — современный PostgreSQL driver с хорошей поддержкой SQLAlchemy.

Для первого спринта выбран синхронный стек:

- он проще для поддержки
- не усложняет код лишней асинхронной инфраструктурой
- полностью достаточен для одного endpoint и транзакционной записи
- позволяет сохранить всю заявку в одной предсказуемой транзакции

## Структура проекта

```text
app/
  api/routes/
  core/
  db/
  repositories/
  schemas/
  services/
docs/
sql/
.env.example
requirements.txt
README.md
```

## Переменные окружения

Используются переменные:

- `FSTR_DB_HOST`
- `FSTR_DB_PORT`
- `FSTR_DB_LOGIN`
- `FSTR_DB_PASS`
- `FSTR_DB_NAME`

Скопируйте `.env.example` в `.env` и заполните значениями своей БД.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Создание схемы БД

Примените SQL из файла:

```bash
psql -U postgres -d database -f sql/schema.sql
```

## Запуск API

```bash
uvicorn app.main:app --reload
```

## Endpoint

### POST `/submitData`

Принимает JSON с данными перевала, пользователя, координат, уровней сложности и изображений.

Новая запись всегда создаётся со статусом модерации `new`.

### Успешный ответ

```json
{
  "status": 200,
  "message": null,
  "id": 42
}
```

На успехе выбран `message = null`, потому что это чище для API-контракта:

- клиенту удобно проверять только `status` и `id`
- поле `message` используется только для ошибок
- ответ остаётся предсказуемым и машинно-ориентированным

### Ошибка валидации

```json
{
  "status": 400,
  "message": "Отсутствует обязательное поле title",
  "id": null
}
```

### Ошибка сервера

```json
{
  "status": 500,
  "message": "Ошибка подключения к базе данных",
  "id": null
}
```

## Пример запроса

```json
{
  "beauty_title": "пер. ",
  "title": "Пхия",
  "other_titles": "Триев",
  "connect": "",
  "add_time": "2021-09-22 13:18:13",
  "user": {
    "email": "qwerty@mail.ru",
    "fam": "Пупкин",
    "name": "Василий",
    "otc": "Иванович",
    "phone": "+7 555 55 55"
  },
  "coords": {
    "latitude": "45.3842",
    "longitude": "7.1525",
    "height": 1200
  },
  "level": {
    "winter": "",
    "summer": "1А",
    "autumn": "1А",
    "spring": ""
  },
  "images": [
    {
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAUA",
      "title": "Седловина"
    }
  ]
}
```

## Пример `curl`

```bash
curl -X POST http://127.0.0.1:8000/submitData ^
  -H "Content-Type: application/json" ^
  -d @request.json
```

## Git-рекомендации

В текущей папке git не инициализирован, поэтому ветку я не создавал. Для нормальной работы рекомендую:

```bash
git init
git checkout -b submitData
```

Логичные коммиты:

```text
feat(db): design normalized schema for mountain pass submissions
feat(api): add POST submitData endpoint with validation and error handling
feat(service): implement transactional mountain pass submission flow
docs(readme): add setup, env, API usage, and sprint-1 architecture notes
```
