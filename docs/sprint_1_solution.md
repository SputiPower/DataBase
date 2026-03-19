# Sprint 1 Solution

## 1. Краткий анализ задачи

Первый спринт проекта `DataBase` решает один транзакционный сценарий: мобильный клиент отправляет данные о горном перевале, а backend валидирует входной JSON, сохраняет нормализованные данные в PostgreSQL и возвращает предсказуемый API-ответ.

Ключевые инженерные цели для спринта:

- не хранить бизнес-сущность в одном `json` поле
- обеспечить атомарное сохранение перевала и всех зависимых сущностей
- оставить кодовую базу готовой к следующим спринтам: модерация, обновление записей, поиск, аналитика

## 2. Анализ проблем исходной структуры БД

Проблемы исходной схемы ФСТР:

- `raw_data json` ломает реляционную модель и лишает БД нормальных ограничений
- `images json` в основной таблице мешает работать с изображениями как с отдельной коллекцией
- отсутствуют явные внешние ключи между перевалом и вложенными сущностями
- нет безопасного статуса модерации
- невозможно гарантировать корректность координат и высоты на уровне БД
- неудобно переиспользовать пользователя и не плодить дубликаты
- структура плохо масштабируется для модерации, фильтрации и отчётности

Вывод: для production-ready backend-а нужна нормализованная схема с отдельными таблицами и ограничениями целостности.

## 3. Улучшенная схема БД

Выбрана следующая реляционная модель:

- `users`
  - отправители данных
  - уникальность по `email`
- `mountain_passes`
  - основная заявка на перевал
  - содержит статус модерации и ссылку на пользователя
- `pass_coordinates`
  - отдельная таблица 1:1 для координат и высоты
- `pass_levels`
  - отдельная таблица 1:1 для уровней сложности по сезонам
- `pass_images`
  - отдельная таблица 1:N для фотографий и их порядка

Причины такой схемы:

- доменные сущности разделены логически и физически
- на каждую часть можно наложить точные ограничения
- связи прозрачны и расширяемы
- структура готова к росту API без болезненных миграций

## 4. Обоснование архитектурных решений

### Почему выбран PostgreSQL ENUM для статуса

Для поля `status` выбран PostgreSQL `ENUM` `mountain_pass_status`.

Почему это лучший вариант здесь:

- список статусов фиксирован и доменно стабилен
- база сама защищает данные от невалидных значений
- запросы и индексы остаются простыми и быстрыми
- это лучше, чем свободный `VARCHAR`, и выразительнее, чем абстрактный `CHECK`

Статусы:

- `new`
- `pending`
- `accepted`
- `rejected`

По умолчанию при создании записи проставляется `new`.

### Почему изображения хранятся в `BYTEA`

Для первого спринта изображения сохраняются в PostgreSQL как `BYTEA`.

Почему именно так:

- JSON контракта уже присылает данные изображения встроенно
- не нужен отдельный файловый сервис или object storage
- вся операция остаётся атомарной в одной транзакции
- нет риска, что запись о перевале появится, а файл физически не сохранится

Для следующего этапа проект легко мигрируется на S3/MinIO с хранением в БД только метаданных и URL.

### Почему пользователь переиспользуется по email

Email выбран как естественный уникальный бизнес-ключ пользователя.

Логика:

- если пользователь с таким `email` уже существует, дубликат не создаётся
- контактные данные обновляются актуальными значениями из нового запроса
- это снижает шум в данных и сохраняет нормальную аналитику по отправителю

## 5. Структура проекта

```text
app/
  api/
    routes/
      passes.py
  core/
    config.py
    database.py
    exceptions.py
  db/
    base.py
    enums.py
    models.py
  repositories/
    pass_repository.py
  schemas/
    pass_submission.py
  services/
    pass_service.py
  main.py
docs/
  architecture.md
  database_analysis.md
  sprint_1_solution.md
sql/
  schema.sql
```

Слои разделены так:

- `core` — конфиг, инфраструктура, исключения
- `db` — ORM и базовая мета-модель
- `repositories` — доступ к данным
- `services` — транзакционный бизнес-сценарий
- `api` — HTTP-контракт
- `schemas` — входные и выходные модели API

## 6. Полный код проекта

Основной код спринта находится в:

- `app/main.py`
- `app/api/routes/passes.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/exceptions.py`
- `app/db/models.py`
- `app/repositories/pass_repository.py`
- `app/services/pass_service.py`
- `app/schemas/pass_submission.py`

SQL-схема вынесена отдельно в `sql/schema.sql`.

## 7. SQLAlchemy models

В ORM-модели реализовано:

- отдельные сущности для пользователя, перевала, координат, уровней и фотографий
- `relationship` для связей `1:N` и `1:1`
- индексы по статусу, времени добавления, пользователю и изображениям
- `CHECK`-ограничения для координат, высоты, непустых обязательных строк и порядка фотографий
- уникальность по `users.email`
- уникальность `pass_images(mountain_pass_id, position)` для детерминированного порядка фотографий

Модели находятся в `app/db/models.py`.

## 8. Pydantic schemas

Схемы находятся в `app/schemas/pass_submission.py` и включают:

- `UserSchema`
- `CoordinatesSchema`
- `LevelSchema`
- `ImageSchema`
- `PassSubmissionSchema`
- `SubmitDataResponse`

Что валидируется:

- обязательные поля
- корректный `email`
- формат `phone`
- диапазоны координат
- неотрицательная высота
- наличие хотя бы одного изображения
- корректность base64 изображения
- приведение пустых строк в optional-полях к `null`-логике

## 9. DB config через env

Подключение к БД берётся из переменных:

- `FSTR_DB_HOST`
- `FSTR_DB_PORT`
- `FSTR_DB_LOGIN`
- `FSTR_DB_PASS`
- `FSTR_DB_NAME`

Чтение настроек реализовано в `app/core/config.py` через `pydantic-settings`.

Пример `.env`:

```env
FSTR_DB_HOST=localhost
FSTR_DB_PORT=5432
FSTR_DB_LOGIN=postgres
FSTR_DB_PASS=postgres
FSTR_DB_NAME=database
```

## 10. Repository / service layer

### Repository

`app/repositories/pass_repository.py` отвечает за:

- поиск или создание пользователя
- создание перевала
- создание координат
- создание уровней сложности
- создание фотографий

### Service

`app/services/pass_service.py` отвечает за orchestration сценария `submitData`.

Он открывает одну транзакцию и гарантирует атомарность всей операции.

Если любая часть сохранения падает:

- транзакция откатывается
- частично сохранённых данных не остаётся

## 11. FastAPI endpoint POST /submitData

Endpoint реализован в `app/api/routes/passes.py`.

Контракт:

- метод: `POST`
- путь: `/submitData`
- принимает JSON согласно `PassSubmissionSchema`
- сохраняет заявку со статусом `new`
- возвращает:

```json
{
  "status": 200,
  "message": null,
  "id": 42
}
```

## 12. Обработка ошибок

Централизованная обработка ошибок настроена в `app/main.py`.

Поддержаны сценарии:

- невалидный JSON
- отсутствие обязательных полей
- ошибки Pydantic-валидации
- ошибки подключения к БД
- ошибки записи в БД
- непредвиденные server-side ошибки

Формат ответа стабилен:

```json
{
  "status": 400,
  "message": "Отсутствует обязательное поле title",
  "id": null
}
```

или

```json
{
  "status": 500,
  "message": "Ошибка подключения к базе данных",
  "id": null
}
```

## 13. Пример .env

См. файл `.env.example`.

```env
FSTR_DB_HOST=localhost
FSTR_DB_PORT=5432
FSTR_DB_LOGIN=postgres
FSTR_DB_PASS=postgres
FSTR_DB_NAME=database
```

## 14. Пример запуска

1. Создать виртуальное окружение и установить зависимости:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Создать схему БД:

```bash
psql -U postgres -d database -f sql/schema.sql
```

3. Запустить API:

```bash
uvicorn app.main:app --reload
```

## 15. Пример запроса

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
    },
    {
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAUB",
      "title": "Подъём"
    }
  ]
}
```

## 16. Пример ответа

Успех:

```json
{
  "status": 200,
  "message": null,
  "id": 42
}
```

Ошибка валидации:

```json
{
  "status": 400,
  "message": "coords.latitude: Широта должна быть в диапазоне от -90 до 90",
  "id": null
}
```

Ошибка БД:

```json
{
  "status": 500,
  "message": "Ошибка подключения к базе данных",
  "id": null
}
```

## 17. Рекомендации по Git-ветке и коммитам

Если репозиторий ещё не инициализирован:

```bash
git init
git checkout -b submitData
```

Рекомендуемая последовательность коммитов:

1. `chore(project): initialize fastapi sprint-1 structure`
2. `feat(db): design normalized postgres schema for mountain passes`
3. `feat(models): add sqlalchemy models and moderation status enum`
4. `feat(schemas): add submitData request and response validation`
5. `feat(service): implement transactional mountain pass submission flow`
6. `feat(api): add POST submitData endpoint and unified error handling`
7. `docs(readme): describe setup, env configuration, and api usage`

Эта разбивка даёт чистую историю разработки и хорошо смотрится на технической проверке.
