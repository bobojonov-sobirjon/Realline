# Пункт 4 — загородная недвижимость (дачи, коттеджи)

Документ описывает, что сделано на **бэкенде** по правкам карточки объекта для подкатегорий **«Дачи»** и **«Коттеджи»**.

---

## Кратко

| Было | Стало |
|------|--------|
| Дачи и коттеджи использовали общий блок «Жилая недвижимость» (как новостройки) | Отдельный блок **`suburban_details`** |
| В админке те же поля, что у новостроек (застройщик, класс жилья, срок сдачи) | Для дач/коттеджей эти поля **не показываются** |
| Один набор фильтров для всех типов | Добавлены фильтры **`house_type`**, **`external_finishing`** |

**Важно:** кнопка «Записаться на просмотр» и вёрстка карточки на сайте — задача **фронтенда**, не этого репозитория.

---

## Категории

Структура витрины:

- **Основная категория:** «Загородная недвижимость» (`slug: suburban`) — только группа, **на объект не назначается**.
- **Подкатегории для объектов:**
  - «Дачи» (`slug: dacha`)
  - «Коттеджи» (`slug: cottage`)
  - «Земельные участки» (`slug: land_plot`) — отдельный блок, как и раньше.

В админке при создании объекта в поле «Категория» доступны только **листовые** категории (без дочерних).

---

## Модель `SuburbanListingDetails`

Новая таблица для блока загорода (OneToOne с `PropertyListing`).

### Поля

| Поле | Тип | Описание |
|------|-----|----------|
| `house_type` | choice | Тип дома |
| `external_finishing` | choice | Внешняя отделка |
| `contract_form` | string | Форма договора |
| `payment_methods` | text | Способы оплаты |
| `travel_time_note` | string | Подпись про дорогу до города |
| `plot_location_text` | text | Доп. текст к локации |

### `house_type` — варианты

| Значение API | Подпись |
|--------------|---------|
| `brick` | Кирпичный |
| `gas_concrete` | Газобетон / пеноблок |
| `wood` | Деревянный |
| `frame` | Каркасный |
| `monolith` | Монолитный |
| `combined` | Комбинированный |

### `external_finishing` — варианты

| Значение API | Подпись |
|--------------|---------|
| `facade_plaster` | Фасадная штукатурка |
| `siding_panels` | Сайдинг и панели |
| `facade_tile` | Фасадная плитка |
| `brick_stone` | Кирпич / камень |
| `wood_cladding` | Облицовка дерево |

---

## Поля на самом объекте (`PropertyListing`)

Для загорода используются поля карточки (не в `suburban_details`):

| Поле | Назначение (п.4) |
|------|------------------|
| `land_area` | Площадь участка, сот. |
| `gas_supply` | Газ (**новое поле**) |
| `electricity_supply` | Электричество |
| `water_supply` | Водоснабжение |
| `communications` | Коммуникации (общая строка) |
| `highway` | Шоссе (FK → справочник) |
| `distance_to_mkad_km` | км от МКАД |
| `address` | Адрес |

Поле **`finishing`** (внутренняя отделка) для дач/коттеджей в админке **скрыто**; вместо него — **`external_finishing`** в блоке загорода.

---

## Что убрано для дач/коттеджей

В блоке **`residential_details`** для категорий `dacha` и `cottage` **не используется**:

- застройщик (`developer`)
- класс жилья (`housing_class`)
- срок сдачи (`completion_period_text`)

Эти поля остаются только для новостроек/вторички (`residential_details`).

---

## Админ-панель

### Как проверить

1. **Объекты недвижимости** → создать или открыть объект.
2. **Категория:** выбрать **«Дачи»** или **«Коттеджи»** (не «Загородная недвижимость»).
3. Нажать **Сохранить** и обновить страницу (F5).
4. Внизу появится блок **«Загородная недвижимость»**:
   - тип дома, внешняя отделка;
   - договор, оплата, дорога, доп. текст по локации.
5. В блоках выше:
   - **Адрес и карта** — шоссе, адрес, км от МКАД;
   - **Площади и дом** — площадь участка;
   - **Коммуникации** — газ, электричество, вода.

### Поведение по категориям

| Категория | Inline-блок в админке |
|-----------|------------------------|
| Дачи, Коттеджи | `SuburbanListingDetails` |
| Земельные участки | `LandPlotListingDetails` |
| Новостройки, вторичка и др. | `ResidentialListingDetails` |

Лоты ЖК (`PropertyListingUnit`) для дач/коттеджей и участков **не показываются**.

---

## API

### Карточка объекта

```
GET /api/v1/accounts/catalog/properties/{id}/
GET /api/v1/accounts/catalog/properties/{slug}/
```

Для **дач/коттеджей** в ответе:

```json
{
  "id": 37,
  "slug": "astrum",
  "category": { "id": 5, "name": "Дачи", "slug": "dacha", "sort_order": 2 },
  "land_area": "12.00",
  "gas_supply": "магистральный",
  "electricity_supply": "подключено",
  "water_supply": "скважина",
  "highway": { "id": 1, "name": "Минское шоссе", "region": "moscow" },
  "address": "д. Примерово, ул. Лесная, 5",
  "distance_to_mkad_km": "25.0",
  "residential_details": null,
  "land_plot_details": null,
  "suburban_details": {
    "house_type": "brick",
    "house_type_display": "Кирпичный",
    "external_finishing": "siding_panels",
    "external_finishing_display": "Сайдинг и панели",
    "contract_form": "",
    "payment_methods": "",
    "travel_time_note": "До Москвы — 25 мин",
    "plot_location_text": "",
    "plot_location": {
      "land_area": "12.00",
      "highway": { "id": 1, "name": "Минское шоссе", "region": "moscow" },
      "distance_to_mkad_km": "25.0",
      "address": "д. Примерово, ул. Лесная, 5"
    }
  }
}
```

Блок **`plot_location`** — агрегат для раздела «Участок и локация» на сайте (площадь, шоссе, МКАД, адрес).

### Создание/редактирование (кабинет агента)

В теле запроса для дач/коттеджей передаётся объект **`suburban_details`**, не `residential_details`:

```json
{
  "category_id": 5,
  "name": "Дача у леса",
  "price": "15000000.00",
  "land_area": "15.00",
  "gas_supply": "есть",
  "electricity_supply": "есть",
  "water_supply": "скважина",
  "highway_id": 1,
  "address": "д. Примерово",
  "distance_to_mkad_km": "30.0",
  "suburban_details": {
    "house_type": "wood",
    "external_finishing": "wood_cladding"
  }
}
```

### Фильтры каталога (загород)

```
GET /api/v1/accounts/catalog/properties/?category_slug=dacha
GET /api/v1/accounts/catalog/properties/?category_slug=cottage
GET /api/v1/accounts/catalog/properties/?house_type=brick
GET /api/v1/accounts/catalog/properties/?external_finishing=facade_plaster
GET /api/v1/accounts/catalog/properties/?land_area_min=10&land_area_max=50
GET /api/v1/accounts/catalog/properties/?distance_to_mkad_max=40
```

---

## Миграции

| Файл | Содержание |
|------|------------|
| `0019_suburban_listing_details` | Модель `SuburbanListingDetails`, поле `gas_supply`, перенос данных с дач/коттеджей из `residential_details` |
| `0020_repair_listing_slug_and_gas` | Починка `slug` / `gas_supply`, если миграции применялись с `--fake` |

На сервере после деплоя:

```bash
python manage.py migrate
```

---

## Что остаётся для фронтенда

- [ ] Карточка: при `category.slug` ∈ `dacha`, `cottage` рендерить **`suburban_details`**, скрыть поля новостройки.
- [ ] Блок «Участок и локация» из `suburban_details.plot_location` + коммуникации с корня объекта.
- [ ] URL каталога: `/catalog/{slug}` вместо `/catalog/{id}`.
- [ ] Кнопка CTA: текст **«Записаться на просмотр»** (сейчас только на фронте).
- [ ] Фильтры каталога загорода: `house_type`, `external_finishing`, площадь участка, МКАД.

---

## Связанные изменения (не п.4, но в том же релизе)

- Иерархия категорий main/sub в админке и API `GET /catalog/categories/`.
- `slug` объекта для ЧПУ-ссылок.
- Уведомление в админке о новых заявках агентов.

---

*Дата документа: июнь 2026*
