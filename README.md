### Мини‑проект «REST API для коллекции видеоигр с учётом времени и достижений» (1 неделя, индивидуальный)

#### 1. Общие сведения

* **Название:** Game Collection Tracker API.
* **Тип:** веб‑приложение (REST API), индивидуальный.
* **Срок:** 1 неделя (5–7 рабочих дней).
* **Цель:** создать REST API для учёта личной коллекции видеоигр с возможностью отслеживания времени игры, достижений и получения данных о играх через сторонний API.

#### 2. Задание проекта (ТЗ)

**Добавленные функциональные требования:**
* учёт времени, проведённого в игре (в минутах/часах);
* добавление достижений для каждой игры (название, описание, дата получения, статус «получено/не получено»);
* просмотр статистики: общее время во всех играх, количество достижений по играм;
* фильтрация игр по количеству достижений и времени игры.

**Остальные функциональные требования (из предыдущей версии):**
* регистрация и авторизация пользователей (JWT);
* CRUD для игр в личной коллекции;
* присвоение рейтингов (1–10) и тегов (жанр, платформа) играм;
* поиск по названию и фильтрация по тегам/рейтингам;
* интеграция со сторонним игровым API (RAWG API или IGDB);
* пагинация списка игр (10 игр на страницу);
* хранение данных в SQLite через ORM;
* документация API (Swagger/ReDoc);
* управление зависимостями через `requirements.txt`.

#### 3. Программный код

**Обновлённая структура проекта** (добавлен модуль для достижений):
```
game-collection-api/
├── app/
│   ├── __init__.py
│   ├── models.py          # ORM‑модели (SQLAlchemy)
│   ├── routes.py         # API‑эндпоинты
│   ├── auth.py          # авторизация (JWT)
│   ├── external_api.py  # интеграция с RAWG API
│   ├── achievements.py  # работа с достижениями
│   └── utils.py         # вспомогательные функции
├── tests/
│   ├── test_auth.py
│   ├── test_games.py
│   └── test_achievements.py
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

**Обновлённые модели данных (`models.py`):**
```python
class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    platform = Column(String)
    release_date = Column(Date)
    user_id = Column(Integer, ForeignKey('users.id'))
    rating = Column(Integer)  # 1–10
    tags = Column(String)  # через запятую: "RPG, Adventure"
    play_time_minutes = Column(Integer, default=0)  # время в минутах
    external_id = Column(Integer)  # ID во внешнем API

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    name = Column(String, nullable=False)  # название достижения
    description = Column(String)  # описание
    date_earned = Column(Date)  # дата получения
    is_earned = Column(Boolean, default=False)  # статус
```

#### 4. API эндпоинты (префикс `/api`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/register`, `/api/login` | Auth |
| GET/POST/PUT/DELETE | `/api/games` | CRUD collection |
| GET | `/api/games/{id}` | Detail |
| PATCH | `/api/games/{id}/playtime` | Add minutes |
| POST | `/api/games/{id}/achievements` | Add achievement |
| PUT | `/api/achievements/{id}` | Update achievement |
| DELETE | `/api/achievements/{id}` | Delete achievement |
| GET | `/api/stats` | Aggregate stats |
| GET | `/api/search` | Search/filter games |

#### 5. Примеры curl запросов

**Auth**
```bash
# Регистрация
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"secret1234"}'

# Логин
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secret1234"}'
```

**Games**
```bash
# Создать игру
curl -X POST http://localhost:8000/api/games \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title":"Elden Ring","platform":"PC","tags":"RPG,Souls-like","rating":9,"play_time_minutes":3600}'

# Список игр (пагинация)
curl "http://localhost:8000/api/games?page=1&size=10" \
  -H "Authorization: Bearer <TOKEN>"

# Детали игры
curl http://localhost:8000/api/games/1 \
  -H "Authorization: Bearer <TOKEN>"

# Обновить игру
curl -X PUT http://localhost:8000/api/games/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"rating":10,"tags":"RPG,Souls-like,Open World"}'

# Удалить игру
curl -X DELETE http://localhost:8000/api/games/1 \
  -H "Authorization: Bearer <TOKEN>"
```

**Playtime**
```bash
# Добавить время игры
curl -X PATCH http://localhost:8000/api/games/1/playtime \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"minutes_to_add":120}'
```

**Achievements**
```bash
# Добавить достижение
curl -X POST http://localhost:8000/api/games/1/achievements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"name":"Roundtable","description":"Reached Roundtable Hill","is_earned":true}'

# Обновить достижение
curl -X PUT http://localhost:8000/api/achievements/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"is_earned":true}'

# Удалить достижение
curl -X DELETE http://localhost:8000/api/achievements/1 \
  -H "Authorization: Bearer <TOKEN>"
```

**Stats & Search**
```bash
# Получить статистику
curl http://localhost:8000/api/stats \
  -H "Authorization: Bearer <TOKEN>"

# Поиск игр (RAWG)
curl "http://localhost:8000/api/search?q=elden+ring&limit=5"
```

#### 7. Пояснительная записка (обновлённая часть)

**Новые ключевые функции:**
* **Учёт времени:** пользователь может добавлять минуты, проведённые в игре, через эндпоинт `PATCH /api/games/{id}/playtime`. Время суммируется.
* **Достижения:** для каждой игры можно:
    * добавлять новые достижения (название, описание);
    * отмечать достижение как «полученное» с указанием даты;
    * редактировать/удалять достижения.
* **Статистика:** эндпоинт `GET /api/stats` возвращает:
    * общее время игры во всех играх (в часах и минутах);
    * количество полученных достижений;
    * топ‑3 самых «потраченных» игр по времени;
    * процент завершённости достижений по каждой игре.

**Реализация:**
* время хранится в минутах в поле `play_time_minutes` модели `Game`;
* достижения связаны с игрой через внешний ключ `game_id`;
* для удобства отображения время конвертируется в часы и минуты на уровне API;
* статистика рассчитывается динамически при запросе `/stats`.

#### 8. Этапы разработки (1 неделя)

| День | Задача |
|------|------|
| 1 | Проектирование БД и API. Создание структуры проекта. Настройка окружения. Выбор внешнего API. |
| 2 | Реализация моделей (SQLAlchemy): `User`, `Game`, `Achievement`. Настройка подключения к БД. |
| 3 | Реализация авторизации (регистрация, вход, JWT). Написание базовых тестов для auth. |
| 4 | Реализация CRUD для игр. Интеграция с внешним API (поиск игр). |
| 5 | Реализация функционала достижений: CRUD, связь с играми. Написание тестов для достижений. |
| 6 | Реализация учёта времени и статистики. Финальное тестирование. Исправление ошибок. Подготовка README. |
| 7 | Развёртывание на хостинге. Подготовка презентации и пояснительной записки. |

#### 9. Презентация (обновлённые слайды)

**Слайд 6. Новые функции: время и достижения**
* скриншоты новых эндпоинтов в Swagger;
* примеры запросов:
    * обновление времени: `PATCH /api/games/1/playtime` → `{"minutes_to_add": 120}`;
    * добавление достижения: `POST /api/games/1/achievements` → `{"name": "First Blood", "is_earned": true}`;
    * статистика: `GET /api/stats` → `{"total_play_time_minutes": 2700, "total_play_time_hours": 45.0, "total_achievements": 23, "earned_achievements": 15}`.

**Слайд 7. Статистика и аналитика**
* диаграмма: топ‑3 игр по времени;
* круговая диаграмма: процент завершённости достижений;
* таблица: игры с наибольшим количеством достижений.

**Слайд 8. Тестирование**
* покрытие тестами: auth, games, achievements, stats;
* результаты: все тесты проходят.

**Слайд 9. Развёртывание**
* хостинг: Railway/Heroku;
* ссылка на работающий сервис;
* инструкция по запуску локально (из README).

**Слайд 10. Заключение**
* достигнутые цели: полный функционал API с учётом времени и достижений;
* сложности: синхронизация данных с внешним API, расчёт статистики;
* планы по развитию:
    * интеграция с Steam API для автоматического получения достижений;
    * графики прогресса по времени и достижениям;
    * уведомления о новых достижениях в играх.

#### 10. Сдача проекта

**Формат сдачи:**
* Git‑репозиторий (GitHub/GitLab) с доступом для преподавателя;
* ссылка на репозиторий в качестве решения задачи;
* папка docs/ с:
    * пояснительной запиской (PDF, 2–3 страницы);
    * презентацией (PDF/PPTX);
* видеодемонстрация (опционально, 1–2 минуты): показать добавление игры, учёт времени, добавление достижения, просмотр статистики.

#### 11. Ожидаемые результаты и оценка

**Соответствие критериям оценивания:**
* **Объём кода:** 400–500 строк → 14 баллов.
* **Чистота кода:** PEP 8, говорящие имена, отсутствие copy‑paste → 5 баллов.
* **Качество проектирования:** модульная архитектура, использование классов и ORM → 20 баллов.
* **Применённые технологии:** FastAPI, SQLAlchemy, JWT, SQLite, pytest, Railway, requests → 20 баллов.
* **Оригинальная идея:** игровой проект с учётом времени и достижений → 9 баллов.
* **Соблюдение сроков:** выполнение всех этапов в срок → 15 баллов.
* **Защита:** чёткое изложение, ответы на вопросы → 10 баллов.
* **Работоспособность:** полный функционал, стабильность → коэффициент 1.
* **Премия:** за развёртывание, документацию и статистику → 4–5 баллов.

---

**Итог:** проект соответствует критериям оценивания для недельного индивидуального задания, имеет игровую тематику и включает функционал учёта времени и достижений, что делает его более интересным и практичным.
