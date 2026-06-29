# Фильтр объектов по городу (Москва / СПб) — для фронтенда

## Задача

На сайте при переключении города в шапке (Москва ↔ Санкт-Петербург) в каталоге должны показываться **только объекты этого города**. В админке у каждого объекта задаётся поле **«Регион витрины»** (`moscow` или `saint_petersburg`).

---

## Что нужно сделать на фронте

При **каждом** запросе каталога передавать query-параметр региона — тот же город, что выбран пользователем в шапке.

> **Важно:** без этого параметра API вернёт **все** опубликованные объекты (и московские, и питерские).

---

## Основной endpoint

```
GET /api/v1/accounts/catalog/properties/
```

### Параметры фильтра по городу (достаточно одного)

| Параметр | Пример | Описание |
|---|---|---|
| `region` | `moscow` | Рекомендуемый вариант |
| `region` | `saint_petersburg` | Санкт-Петербург |
| `site_region_slug` | `saint-petersburg` | Slug из `GET /api/v1/site/regions/` |
| `country` | `moscow` | Legacy-алиас (как у районов/шоссе) |

### Поддерживаемые значения

**Москва:** `moscow`, `msk`

**Санкт-Петербург:** `saint_petersburg`, `saint-petersburg`, `spb`, `st-petersburg`, `petersburg`

### Примеры запросов

```http
GET /api/v1/accounts/catalog/properties/?region=moscow
GET /api/v1/accounts/catalog/properties/?region=saint_petersburg
GET /api/v1/accounts/catalog/properties/?site_region_slug=saint-petersburg
GET /api/v1/accounts/catalog/properties/?region=moscow&category=3&price_max=5000000
```

Параметр `region` можно комбинировать с остальными фильтрами каталога (`category`, `district`, `price_min`, `price_max` и т.д.).

---

## Поле в ответе

В каждом объекте каталога есть поле `region`:

```json
{
  "id": 37,
  "slug": "astrum",
  "name": "Аструм",
  "region": "moscow"
}
```

Значения: **`moscow`** или **`saint_petersburg`**.

Можно использовать для проверки или отображения, но основная фильтрация — через query-параметр при запросе списка.

---

## Связь с выбором города на сайте

Список городов в шапке:

```
GET /api/v1/site/regions/
```

Пример ответа:

```json
[
  { "id": 1, "name": "Москва", "slug": "moscow" },
  { "id": 2, "name": "Санкт-Петербург", "slug": "saint-petersburg" }
]
```

### Рекомендуемая логика

1. Пользователь выбирает город → сохраняете `slug` (например `saint-petersburg`).
2. При запросе каталога передаёте:
   - `?site_region_slug=saint-petersburg` **или**
   - `?region=saint_petersburg` (если маппите slug → значение API).

Пример маппинга:

```javascript
const regionParam = selectedSlug === 'moscow'
  ? 'moscow'
  : 'saint_petersburg';

fetch(`/api/v1/accounts/catalog/properties/?region=${regionParam}`);
```

---

## Справочники районов и шоссе

При фильтрах по локации тоже передавайте регион — иначе в выпадающих списках будут районы/шоссе обоих городов.

```http
GET /api/v1/accounts/catalog/districts/?region=moscow
GET /api/v1/accounts/catalog/districts/?region=saint_petersburg

GET /api/v1/accounts/catalog/highways/?region=moscow
GET /api/v1/accounts/catalog/highways/?region=saint_petersburg
```

В ответе у каждой записи есть поле `region`.

---

## Карточка объекта (detail)

```
GET /api/v1/accounts/catalog/properties/{slug}/
GET /api/v1/accounts/catalog/properties/{id}/
```

Открывается по slug или id **без фильтра по региону** (прямая ссылка работает). В теле ответа есть поле `region` — при необходимости можно скрыть карточку или показать сообщение, если `region` не совпадает с выбранным городом.

---

## Чеклист для фронта

- [ ] При смене города в шапке обновлять запросы каталога с `region` или `site_region_slug`
- [ ] Передавать тот же регион в `districts` и `highways`, если они зависят от города
- [ ] Не полагаться только на клиентскую фильтрацию — фильтрация на бэкенде
- [ ] Hero-слайды уже фильтруются по `site_region` / `site_region_slug` — та же логика города

---

## Swagger

Описание фильтра есть в Swagger: **Каталог → GET /catalog/properties/**, параметр `region`.

---

---

# Obyektlarni shahar bo‘yicha filtrlash (Moskva / SPb) — frontend uchun

## Vazifa

Saytda shapka (header) da shahar almashtirilganda (Moskva ↔ Sankt-Peterburg) katalogda **faqat shu shaharga tegishli obyektlar** ko‘rsatilishi kerak. Admin panelda har bir obyekt uchun **«Регион витрины»** (`moscow` yoki `saint_petersburg`) belgilanadi.

---

## Frontendda nima qilish kerak

Katalogga **har safar** so‘rov yuborilganda region query-parametri yuborilishi shart — foydalanuvchi shapka da tanlagan shahar bilan bir xil.

> **Muhim:** bu parametr bo‘lmasa API **barcha** nashr etilgan obyektlarni qaytaradi (ham Moskva, ham SPb).

---

## Asosiy endpoint

```
GET /api/v1/accounts/catalog/properties/
```

### Shahar filtri parametrlari (bittasi yetarli)

| Parametr | Misol | Tavsif |
|---|---|---|
| `region` | `moscow` | Tavsiya etiladi |
| `region` | `saint_petersburg` | Sankt-Peterburg |
| `site_region_slug` | `saint-petersburg` | `GET /api/v1/site/regions/` dan slug |
| `country` | `moscow` | Legacy alias (tumanlar/shosse kabi) |

### Qo‘llab-quvvatlanadigan qiymatlar

**Moskva:** `moscow`, `msk`

**Sankt-Peterburg:** `saint_petersburg`, `saint-petersburg`, `spb`, `st-petersburg`, `petersburg`

### So‘rov misollari

```http
GET /api/v1/accounts/catalog/properties/?region=moscow
GET /api/v1/accounts/catalog/properties/?region=saint_petersburg
GET /api/v1/accounts/catalog/properties/?site_region_slug=saint-petersburg
GET /api/v1/accounts/catalog/properties/?region=moscow&category=3&price_max=5000000
```

`region` parametrini boshqa katalog filtrlari bilan birga ishlatish mumkin (`category`, `district`, `price_min`, `price_max` va hokazo).

---

## Javobdagi maydon

Har bir obyektda `region` maydoni bor:

```json
{
  "id": 37,
  "slug": "astrum",
  "name": "Аструм",
  "region": "moscow"
}
```

Qiymatlar: **`moscow`** yoki **`saint_petersburg`**.

Tekshirish yoki ko‘rsatish uchun ishlatish mumkin, lekin asosiy filtrlash — ro‘yxat so‘rovida query-parametr orqali.

---

## Saytdagi shahar tanlash bilan bog‘lanish

Shapkadagi shaharlar ro‘yxati:

```
GET /api/v1/site/regions/
```

Javob misoli:

```json
[
  { "id": 1, "name": "Москва", "slug": "moscow" },
  { "id": 2, "name": "Санкт-Петербург", "slug": "saint-petersburg" }
]
```

### Tavsiya etilgan mantiq

1. Foydalanuvchi shahar tanlaydi → `slug` saqlanadi (masalan `saint-petersburg`).
2. Katalog so‘rovida yuboriladi:
   - `?site_region_slug=saint-petersburg` **yoki**
   - `?region=saint_petersburg` (slug → API qiymatiga map qilsangiz).

Mapping misoli:

```javascript
const regionParam = selectedSlug === 'moscow'
  ? 'moscow'
  : 'saint_petersburg';

fetch(`/api/v1/accounts/catalog/properties/?region=${regionParam}`);
```

---

## Tumanlar va shosse ma’lumotnomalari

Lokatsiya filtrlari uchun ham region yuboring — aks holda ikkala shaharning tumanlari/shosselari aralash chiqadi.

```http
GET /api/v1/accounts/catalog/districts/?region=moscow
GET /api/v1/accounts/catalog/districts/?region=saint_petersburg

GET /api/v1/accounts/catalog/highways/?region=moscow
GET /api/v1/accounts/catalog/highways/?region=saint_petersburg
```

Har bir yozuvda `region` maydoni bor.

---

## Obyekt kartochkasi (detail)

```
GET /api/v1/accounts/catalog/properties/{slug}/
GET /api/v1/accounts/catalog/properties/{id}/
```

Slug yoki id bo‘yicha ochiladi, **region filtri yo‘q** (to‘g‘ridan-to‘g‘ri havola ishlaydi). Javobda `region` bor — kerak bo‘lsa, tanlangan shahar bilan mos kelmasa kartochkani yashirish yoki xabar ko‘rsatish mumkin.

---

## Frontend cheklist

- [ ] Shapka da shahar almashtirilganda katalog so‘rovlariga `region` yoki `site_region_slug` qo‘shish
- [ ] `districts` va `highways` ga ham shu regionni yuborish
- [ ] Faqat klient tomonda filtrlashga tayanmaslik — filtrlash backendda
- [ ] Hero-slidelar allaqachon `site_region` / `site_region_slug` bo‘yicha filtrlanadi — shu shahar mantig‘ini qo‘llash

---

## Swagger

Filter tavsifi Swagger’da: **Каталог → GET /catalog/properties/**, `region` parametri.

---

## Qisqa xulosa (o‘zbekcha)

Frontend har safar foydalanuvchi shahar tanlaganda katalog API ga `region=moscow` yoki `region=saint_petersburg` yuborishi **shart** — aks holda barcha obyektlar chiqadi.
