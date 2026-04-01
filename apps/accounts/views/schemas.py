from apps.accounts.filters import (
    CATALOG_TAG_FOREST,
    CATALOG_TAG_PROMO,
    CATALOG_TAG_RAILWAY,
    CATALOG_TAG_START_SALES,
)

_PROPERTY_TAGS_CATALOG_HINT = (
    'Для попадания в фильтры публичного каталога (`GET .../catalog/properties/`) добавьте в `tags` '
    '**точно такие** строки (как в справочнике на backend; при поиске регистр не важен):\n'
    f'- `{CATALOG_TAG_PROMO}` — фильтр `promo=true`\n'
    f'- `{CATALOG_TAG_START_SALES}` — `start_sales=true`\n'
    f'- `{CATALOG_TAG_FOREST}` — `forest_access=true`\n'
    f'- `{CATALOG_TAG_RAILWAY}` — `near_railway=true`\n'
    'Любые другие имена тегов тоже можно передавать — они просто не привязаны к этим query-параметрам.'
)

_PROPERTY_BODY_DESCRIPTION = (
    '**Рекомендуется `multipart/form-data`:** удобно прикреплять файлы. Также поддерживается `application/json` '
    '(без загрузки файлов или с URL вне этого API).\n\n'
    '- Текстовые поля как в форме на сайте.\n'
    '- **images** — одно или несколько полей с именем `images` (несколько файлов).\n'
    '- **tags** — массив **строк**, как **images**: в Swagger «Add string item» / повтор поля `tags` в form-data; '
    'формат JSON в теле: `["тег1","тег2"]` или `[{"tag_name":"имя"}]`. '
    'Переданный набор задаёт **текущие** теги объекта (полная замена из этого запроса для поля `tags`). '
    'Отдельно только теги: `PUT /properties/{id}/tags/`.\n\n'
    f'{_PROPERTY_TAGS_CATALOG_HINT}\n\n'
    '- **district_id**, **highway_id** — из публичных справочников `GET .../catalog/districts/` и `.../catalog/highways/`; '
    '**address** — только вручную (улица, дом).\n'
    '- **area** — площадь дома/объекта, м²; **land_area** — участок, сот.; **distance_to_mkad_km** — до МКАД, км; '
    '**lat**, **long** — широта и долгота для карты (WGS84; в БД хранятся как latitude / longitude).\n'
    '- Флаги посёлка/локации: `has_asphalt_roads`, `has_street_lighting`, `has_guarded_territory`, `near_shops`, '
    '`near_school_kindergarten`, `near_public_transport` (boolean).\n'
    '- Коммуникации по отдельности: `electricity_supply`, `water_supply`, `sewage_type`, `heating_type`, '
    '`internet_connection`; поле **communications** — краткое резюме строкой.\n'
    '- **property_type:** `land`, `house`, `apartment`, `commercial`, `other`.'
)

_PROPERTY_DETAIL_DESCRIPTION = (
    'То же тело, что и при создании: **multipart/form-data** или JSON. '
    'При **PUT** нужно передать полный набор полей; при **PATCH** — только изменённые. '
    'Если передать `images` (включая пустой список), старые фото заменяются; без поля `images` файлы не трогаются.\n\n'
    f'{_PROPERTY_TAGS_CATALOG_HINT}'
)

_CATALOG_DESCRIPTION = (
    'JWT **не обязателен** для доступа к списку. Чтобы в ответе были актуальные **`is_favourite`** и **`is_compare`**, '
    'передайте заголовок **Authorization: Bearer** с access-токеном (в Swagger UI нажмите **Authorize** — иначе UI может не '
    'прикрепить токен к запросу).\n\n'
    'Только объявления со статусом «Опубликован». Упорядочено по дате создания (новые сверху).\n\n'
    '**Query-фильтры (как на сайте):**\n'
    '- `property_type` — `land` | `house` | `apartment` | `commercial` | `other`\n'
    '- `district`, `highway` — **id** из `GET .../catalog/districts/` и `.../catalog/highways/`\n'
    '- `area_min`, `area_max` — площадь дома/объекта, м²\n'
    '- `land_area_min`, `land_area_max` — площадь участка, сот.\n'
    '- `distance_to_mkad_max` — не дальше N км от МКАД (поле `distance_to_mkad_km` объекта ≤ N)\n'
    '- `price_min`, `price_max` — цена, ₽\n'
    '- `has_asphalt_roads`, `has_street_lighting`, `has_guarded_territory`, `near_shops`, '
    '`near_school_kindergarten`, `near_public_transport` — `true` / `false`\n'
    '- `promo`, `start_sales`, `forest_access`, `near_railway` — передать `true`, если нужны объекты с тегом: '
    '«Акция», «Старт продаж», «С выходом в Лес», «Ж/д станция рядом» (те же строки в тегах объекта).\n\n'
    'Пагинация: `limit`, `offset`.'
)
