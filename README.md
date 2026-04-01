# RealEstateRus (Realline)

Backend: **Django 5**, **Django_REST_Framework**, **PostgreSQL**, **JWT** (SimpleJWT), **drf-spectacular** (OpenAPI/Swagger).

## Быстрый старт

### 1. Окружение

```bash
python -m venv env
env\Scripts\activate          # Windows
pip install -r requirements.txt
```

Создайте файл `.env` (или задайте переменные окружения) для БД, например:

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

Значения по умолчанию смотрите в `config/settings.py`.

### 2. Миграции и суперпользователь

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Запуск

```bash
python manage.py runserver
```

- **Админка:** http://127.0.0.1:8000/admin/
- **Swagger:** http://127.0.0.1:8000/docs/
- **OpenAPI schema:** http://127.0.0.1:8000/schema/
- **API:** `http://127.0.0.1:8000/api/v1/accounts/` и `http://127.0.0.1:8000/api/v1/site/`

---

## Наполнение данными (демо)

Команда **`seed_website_demo`** добавляет тестовый контент для публичной витрины и блога. Повторный запуск **безопасен**: существующие записи не дублируются (проверки slug, текста FAQ, флагов и т.д.).

### Полное наполнение (рекомендуется после чистой БД)

```bash
python manage.py seed_website_demo
```

Создаётся:

| Раздел | Что появляется |
|--------|----------------|
| **Контакты** | одна запись `SiteContacts` (только если таблица пустая) |
| **Заявки на консультацию** | несколько демо-заявок с меткой в тексте `[ДЕМО-ЗАЯВКА]` (один раз) |
| **Слайды главной** | 3 `HeroSlide` с заглушками-картинками |
| **Преимущества** | 4 `AdvantageCard` |
| **Услуги** | 3 `ServiceCard` с блоками, шагами, перекрёстными ссылками |
| **Команда** | 4 `TeamMember` |
| **Отзывы** | 5 `ClientReview` |
| **FAQ** | 10 вопросов `FAQEntry` |
| **Статьи блога** | до 4 статей `Article` с блоками и пунктами списка |

### Только часть данных

```bash
python manage.py seed_website_demo --skip-faq              # без FAQ
python manage.py seed_website_demo --skip-articles         # без статей
python manage.py seed_website_demo --skip-showcase         # без витрины (слайды, услуги, отзывы…)
python manage.py seed_website_demo --skip-faq --skip-articles   # только витрина
```

Совместимость со старым именем (делегирует к `seed_website_demo --skip-faq`):

```bash
python manage.py seed_demo_land_article
```

### Ручное наполнение в админке

После `createsuperuser` всё основное редактируется в **Django Admin** (часто с темой Jazzmin):

- **Сайт:** регионы, слайды, преимущества, услуги, FAQ, статьи (блоки статьи — вложенные формы `nested_admin`), команда, отзывы, контакты, заявки.
- **Accounts:** пользователи, объекты недвижимости (`PropertyListing`), районы/шоссе, избранное/сравнение (как модели при необходимости).

**Статьи:** поле `sections` в API формируется из связанных моделей блоков и пунктов списка, не из сырого JSON.

**Объекты недвижимости** можно создавать через API (JWT агента) — см. Swagger, теги `Accounts — объекты` и `Каталог`. В карточке объекта для карты используются поля API **`lat`** и **`long`** (в БД: `latitude`, `longitude`).

---

## Полезные заметки

- Каталог публичный: `GET /api/v1/accounts/catalog/properties/` — без JWT ответ приходит, флаги **`is_favourite`** / **`is_compare`** будут `false`; с **Bearer** — актуальные значения для пользователя.
- Медиафайлы при разработке: `MEDIA_ROOT`, раздача через `runserver` и маршрут в `config/urls.py`.

Для production настройте `ALLOWED_HOSTS`, статику, БД и секретный ключ отдельно от репозитория.
