"""
Демо-данные для сайта: витрина (слайды, преимущества, услуги, команда, отзывы,
контакты, заявки), FAQ и статьи блога.

  python manage.py seed_website_demo
  python manage.py seed_website_demo --skip-faq
  python manage.py seed_website_demo --skip-articles
  python manage.py seed_website_demo --skip-showcase

Повторный запуск безопасен (get_or_create / проверки slug и меток).
"""

import io
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image

from apps.website.models import (
    AdvantageCard,
    Article,
    ArticleSection,
    ArticleSectionItem,
    ClientReview,
    ConsultationLead,
    FAQEntry,
    HeroSlide,
    ServiceBenefitBlock,
    ServiceCard,
    ServiceFeatureLine,
    ServicePillTag,
    ServiceWorkflowStep,
    SiteContacts,
    TeamMember,
)

DEMO_LEAD_MARKER = "[ДЕМО-ЗАЯВКА]"


def _png(color: tuple[int, int, int], size: tuple[int, int] = (1200, 630)) -> ContentFile:
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="PNG")
    return ContentFile(buf.getvalue())


def _seed_site_contacts(stdout, style) -> None:
    if SiteContacts.objects.exists():
        stdout.write(style.WARNING("Контакты: запись уже есть, пропуск."))
        return
    SiteContacts.objects.create(
        phone="+7 (812) 555-12-34",
        email="hello@realestaterus.demo",
        address="Санкт-Петербург, Невский проспект, д. 100, офис 12",
        work_hours="Пн–Пт 9:00–19:00; Сб 11:00–16:00; Вс — выходной",
        telegram_url="https://t.me/example_demo",
        vk_url="https://vk.com/example_demo",
        map_embed_url="",
    )
    stdout.write(style.SUCCESS("Контакты: создана демо-запись."))


def _seed_consultation_leads(stdout, style) -> None:
    if ConsultationLead.objects.filter(message__contains=DEMO_LEAD_MARKER).exists():
        stdout.write(style.WARNING("Заявки: демо-заявки уже есть, пропуск."))
        return
    samples = [
        ("Ирина Смирнова", "+79215550101", "irina.demo@mail.test", "Интересует подбор 3-комн. у метро."),
        ("Алексей Козлов", "+79215550202", "", "Нужна консультация по ипотеке и маткапиталу."),
        ("Марина Волкова", "+79215550303", "marina.demo@mail.test", "Участок под ИЖС в Ленобласти."),
        ("Демо Пётр Николаев", "+79215550404", "", f"{DEMO_LEAD_MARKER} Тестовая заявка из сида."),
    ]
    for name, phone, email, msg in samples:
        ConsultationLead.objects.create(
            name=name,
            phone=phone,
            email=email or "",
            message=msg,
            personal_data_consent=True,
        )
    stdout.write(style.SUCCESS(f"Заявки: создано {len(samples)} демо-записей."))


def _seed_hero_slides(stdout, style) -> None:
    slides = [
        (0, "Недвижимость в Санкт-Петербурге", "Подбор, проверка и сопровождение сделки под ключ."),
        (1, "Ипотека без лишней суеты", "Поможем собрать документы и согласовать сроки с банком."),
        (2, "Земельные участки и загород", "Юридическая проверка и инженерные риски — до договора."),
    ]
    created = 0
    colors = [(44, 62, 80), (52, 152, 219), (46, 204, 113)]
    for (order, title, subtitle), color in zip(slides, colors):
        obj, was_new = HeroSlide.objects.get_or_create(
            title=title,
            defaults={
                "subtitle": subtitle,
                "sort_order": order,
                "is_active": True,
            },
        )
        if was_new:
            obj.image.save(f"demo-hero-{order}.png", _png(color), save=True)
            created += 1
    stdout.write(
        style.SUCCESS(f"Слайды: добавлено новых {created}, всего {HeroSlide.objects.count()}")
    )


def _seed_advantages(stdout, style) -> None:
    cards = [
        (
            0,
            "Опыт и локальная экспертиза",
            "Знаем рынок СПб и Ленобласти: от центра до удалённых участков. Подскажем район под ваш сценарий жизни.",
            (241, 196, 15),
        ),
        (
            1,
            "Проверка документов и рисков",
            "Смотрим ЕГРН, цепочку прав, обременения и типовые «красные флаги» до задатка и сделки.",
            (230, 126, 34),
        ),
        (
            2,
            "Прозрачные условия",
            "Фиксируем этапы работ и состав услуг. Без навязывания — только по вашему запросу.",
            (155, 89, 182),
        ),
        (
            3,
            "Сопровождение сделки",
            "Координируем банк, продавца и нотариуса; помогаем с безопасными расчётами.",
            (26, 188, 156),
        ),
    ]
    created = 0
    for order, title, body, color in cards:
        obj, was_new = AdvantageCard.objects.get_or_create(
            title=title,
            defaults={
                "sort_order": order,
                "body": body,
                "is_active": True,
            },
        )
        if was_new:
            obj.image.save(f"demo-advantage-{order}.png", _png(color, (800, 600)), save=True)
            created += 1
    stdout.write(
        style.SUCCESS(f"Преимущества: добавлено новых {created}, всего {AdvantageCard.objects.count()}")
    )


def _seed_team(stdout, style) -> None:
    members = [
        (0, "Анна Морозова", "Руководитель отдела продаж", "12+ лет в недвижимости"),
        (1, "Дмитрий Соколов", "Юрист по недвижимости", "Сделки и Due Diligence"),
        (2, "Елена Кузнецова", "Ипотечный брокер", "Банки-партнёры, льготные программы"),
        (3, "Михаил Орлов", "Эксперт по загороду", "Участки, коммуникации, градплан"),
    ]
    created = 0
    colors = [(149, 165, 166), (127, 140, 141), (189, 195, 199), (113, 128, 147)]
    for (order, name, role, exp), color in zip(members, colors):
        obj, was_new = TeamMember.objects.get_or_create(
            full_name=name,
            defaults={
                "sort_order": order,
                "role": role,
                "experience": exp,
                "is_active": True,
            },
        )
        if was_new:
            obj.photo.save(f"demo-team-{order}.png", _png(color, (400, 400)), save=True)
            created += 1
    stdout.write(
        style.SUCCESS(f"Команда: добавлено новых {created}, всего {TeamMember.objects.count()}")
    )


def _seed_reviews(stdout, style) -> None:
    reviews = [
        (0, "Светлана П.", "Санкт-Петербург", "Купили квартиру в «сталинке». Помогли с проверкой и ипотекой, всё объяснили по шагам."),
        (1, "Андрей Ф.", "Гатчина", "Подобрали участок под дом. Юрист ответил на все вопросы по ИЖС."),
        (2, "Ольга М.", "СПб", "Быстро организовали просмотры, без навязчивости. Сделку закрыли в срок."),
        (3, "Константин Л.", "Всеволожск", "Отличное сопровождение: банк, оценка, нотариус — одним графиком."),
        (4, "Наталья Ж.", "Санкт-Петербург", "Рекомендую: честно говорят о рисках объекта, а не только о плюсах."),
    ]
    created = 0
    for order, author, city, text in reviews:
        _obj, was_new = ClientReview.objects.get_or_create(
            author_name=author,
            city=city,
            text=text,
            defaults={
                "sort_order": order,
                "is_published": True,
            },
        )
        if was_new:
            created += 1
    stdout.write(
        style.SUCCESS(f"Отзывы: добавлено новых {created}, всего {ClientReview.objects.count()}")
    )


def _seed_services(stdout, style) -> None:
    if ServiceCard.objects.filter(slug="podbor-nedvizhimosti").exists():
        stdout.write(style.WARNING("Услуги: демо-услуги уже есть, пропуск."))
        return

    def create_service(
        *,
        sort_order: int,
        title: str,
        slug: str,
        body: str,
        hero: str,
        color: tuple[int, int, int],
        fname: str,
        features: list[str],
        pills: list[str],
        benefits: list[tuple[str, str]],
        steps: list[tuple[int, str, str]],
    ) -> ServiceCard:
        s = ServiceCard(
            sort_order=sort_order,
            title=title,
            slug=slug,
            body=body,
            hero_text=hero,
            is_active=True,
        )
        s.image.save(fname, _png(color), save=True)
        for i, t in enumerate(features):
            ServiceFeatureLine.objects.create(service=s, sort_order=i, text=t)
        for i, t in enumerate(pills):
            ServicePillTag.objects.create(service=s, sort_order=i, text=t)
        for i, (bt, bb) in enumerate(benefits):
            ServiceBenefitBlock.objects.create(service=s, sort_order=i, title=bt, body=bb)
        for sn, st, sb in steps:
            ServiceWorkflowStep.objects.create(
                service=s, step_number=sn, title=st, body=sb
            )
        return s

    with transaction.atomic():
        s1 = create_service(
            sort_order=0,
            title="Подбор недвижимости",
            slug="podbor-nedvizhimosti",
            body="Короткий брифинг, подбор объектов, организация просмотров и переговоров по цене.",
            hero=(
                "Найдём варианты под ваш бюджет и сценарий: квартира, новостройка или загород. "
                "Сопровождаем на всех этапах до сделки."
            ),
            color=(41, 128, 185),
            fname="demo-service-podbor.png",
            features=[
                "Сбор и уточнение требований",
                "Прескоринг объектов и рисков",
                "Просмотры и сравнительная таблица",
                "Поддержка при торге",
            ],
            pills=["СПб и ЛО", "Вторичка и новостройки", "Ипотека"],
            benefits=[
                (
                    "Экономия времени",
                    "Не нужно отвечать на десятки объявлений — мы отфильтруем шум.",
                ),
                (
                    "Понятный маршрут",
                    "Этапы, сроки и чек-листы — чтобы не забыть важные проверки.",
                ),
            ],
            steps=[
                (1, "Брифинг", "15–30 минут: цели, бюджет, география."),
                (2, "Подборка", "3–7 дней: список объектов с комментариями."),
                (3, "Просмотры и выбор", "Осмотр, переговоры, резервирование."),
                (4, "Сделка", "Документы, банк, нотариус."),
            ],
        )
        s2 = create_service(
            sort_order=1,
            title="Сопровождение сделки",
            slug="soprovozhdenie-sdelki",
            body="Юридическая проверка, организация расчётов и координация участников сделки.",
            hero=(
                "Снижаем правовые и финансовые риски: проверяем объект, договоры и график расчётов."
            ),
            color=(142, 68, 173),
            fname="demo-service-sdelka.png",
            features=[
                "Анализ выписки ЕГРН и документов продавца",
                "Договор купли-продажи / ДДУ — рекомендации",
                "Схема расчётов: аккредитив / ячейка / эскроу",
                "Контроль регистрации перехода права",
            ],
            pills=["Юрист", "Нотариус", "Банк"],
            benefits=[
                ("Меньше стресса", "Один ответственный за координацию сроков."),
                ("Прозрачность", "Поясняем каждый документ простым языком."),
            ],
            steps=[
                (1, "Проверка объекта", "ЕГРН, обременения, правоустанавливающие."),
                (2, "Подготовка пакета", "Для банка и нотариуса."),
                (3, "Сделка", "Подписание и расчёты."),
                (4, "Регистрация", "Контроль загрузки в Росреестр."),
            ],
        )
        s3 = create_service(
            sort_order=2,
            title="Оценка и Due Diligence",
            slug="ocenka-i-proverka",
            body="Глубокая проверка объекта перед задатком: юридика, рыночная конъюнктура, «красные флаги».",
            hero="Для инвесторов и покупателей дорогого жилья — отдельный чек-лист и отчёт.",
            color=(39, 174, 96),
            fname="demo-service-dd.png",
            features=[
                "Сравнение с аналогами на рынке",
                "История цены и типовые риски дома/ЖК",
                "Рекомендации по торгу и условиям",
            ],
            pills=["Отчёт", "Риски", "Рынок"],
            benefits=[
                ("Объективная картина", "Понимаете, за что платите."),
                ("Решение с цифрами", "Опираемся на факты, а не на объявление."),
            ],
            steps=[
                (1, "Запрос данных", "Документы, адрес, ваши опасения."),
                (2, "Анализ", "Юридика + рыночный срез."),
                (3, "Отчёт", "Выводы и рекомендации."),
            ],
        )
        s1.related_services.add(s2, s3)
        s2.related_services.add(s1, s3)
    stdout.write(style.SUCCESS("Услуги: созданы 3 демо-карточки с блоками и шагами."))


def _create_article(
    *,
    slug: str,
    title: str,
    lead: str,
    description: str,
    body: str,
    published_at: date,
    sections: list[dict],
    image_color: tuple[int, int, int],
    image_basename: str,
) -> Article | None:
    if Article.objects.filter(slug=slug).exists():
        return None
    article = Article(
        slug=slug,
        title=title,
        lead=lead[:600],
        description=description[:2000] if description else lead[:350] + "…",
        published_at=published_at,
        body=body,
        is_published=True,
    )
    article.image.save(
        image_basename, _png(image_color), save=False
    )
    article.save()
    for si, block in enumerate(sections):
        sec = ArticleSection.objects.create(
            article=article,
            sort_order=si,
            title=block["title"],
            intro=(block.get("intro") or "")[:5000],
            list_title=(block.get("list_title") or "")[:500],
            closing=(block.get("closing") or "")[:5000],
        )
        for ij, text in enumerate(block.get("items") or []):
            ArticleSectionItem.objects.create(
                section=sec, sort_order=ij, text=text[:1000]
            )
    return article


FAQ_SEED = [
    (
        0,
        "Как записаться на консультацию по недвижимости?",
        "Оставьте заявку на сайте или позвоните по телефону в шапке. Мы согласуем удобное время "
        "очной или онлайн-встречи и подберём специалиста по вашему запросу.",
    ),
    (
        1,
        "Работаете ли вы с ипотекой и материнским капиталом?",
        "Да, помогаем с одобрением ипотеки в банках-партнёрах, подготовкой пакета документов "
        "и использованием материнского капитала в сделке, если это предусмотрено программой.",
    ),
    (
        2,
        "Сколько стоят услуги агентства?",
        "Стоимость зависит от объёма работ: подбор объекта, проверка, сопровождение сделки. "
        "Точные условия обсуждаются после короткого брифинга — без скрытых платежей.",
    ),
    (
        3,
        "Какие документы нужны для покупки квартиры?",
        "Обычно потребуется паспорт, СНИЛС, справки о доходах для ипотеки, а также документы "
        "продавца по объекту. Мы даём чек-лист под вашу ситуацию.",
    ),
    (
        4,
        "Проверяете ли вы юридическую чистоту объекта?",
        "Да: запрашиваем выписку ЕГРН, анализируем историю переходов прав, обременения и риски "
        "до подписания договора.",
    ),
    (
        5,
        "Сколько времени занимает подбор земельного участка?",
        "В среднем от нескольких дней до нескольких недель — в зависимости от бюджета, района "
        "и ограничений по назначению земли.",
    ),
    (
        6,
        "Есть ли сопровождение на сделке у нотариуса?",
        "Да, специалист может присутствовать на сделке, контролировать корректность документов "
        "и расчёты.",
    ),
    (
        7,
        "Работаете только в Санкт-Петербурге и Ленобласти?",
        "Основной фокус — Санкт-Петербург и Ленинградская область; отдельные запросы по другим "
        "регионам обсуждаются индивидуально.",
    ),
    (
        8,
        "Можно ли продать квартиру без показов через агентство?",
        "Да, возможны форматы с ограниченным кругом показов или по предварительной записи. "
        "Условия фиксируются в договоре.",
    ),
    (
        9,
        "Что такое «безопасные расчёты» при сделке?",
        "Это схемы, при которых деньги и документы передаются с учётом рисков: аккредитив, "
        "ячейка, эскроу в банке — мы подскажем оптимальный вариант.",
    ),
]

ARTICLE_LAND_SECTIONS = [
    {
        "title": "1. Назначение земли",
        "intro": (
            "Первое, что нужно проверить — это категория и вид разрешённого использования участка."
        ),
        "list_title": "Для строительства дома подойдут:",
        "items": [
            "ИЖС (индивидуальное жилищное строительство)",
            "ЛПХ (личное подсобное хозяйство)",
        ],
        "closing": (
            "Некоторые участки могут иметь ограничения, при которых строительство будет "
            "невозможно или затруднено."
        ),
    },
    {
        "title": "2. Локация и транспортная доступность",
        "intro": "",
        "list_title": "Обратите внимание на:",
        "items": [
            "расстояние до города",
            "удобство подъезда",
            "наличие общественного транспорта",
        ],
        "closing": (
            "Также важно оценить инфраструктуру: магазины, школы, медицинские учреждения."
        ),
    },
    {
        "title": "3. Коммуникации",
        "intro": "Наличие коммуникаций напрямую влияет на стоимость и комфорт проживания.",
        "list_title": "Проверьте:",
        "items": ["электричество", "водоснабжение", "канализацию", "газ"],
        "closing": (
            "Если коммуникации отсутствуют, уточните возможность и стоимость подключения."
        ),
    },
    {
        "title": "4. Юридическая чистота",
        "intro": "Перед покупкой убедитесь в отсутствии обременений и корректности документов.",
        "list_title": "Проверьте:",
        "items": [
            "регистрацию в Росреестре",
            "комплект правоустанавливающих документов",
            "отсутствие залогов и судебных споров",
        ],
        "closing": "При сомнениях закажите выписку ЕГРН и консультацию юриста.",
    },
    {
        "title": "5. Характеристики участка",
        "intro": "Форма, рельеф и почва влияют на удобство застройки и дренаж.",
        "list_title": "Оцените:",
        "items": ["конфигурацию участка", "рельеф", "тип грунта"],
        "closing": (
            "Неудачная форма или грунт могут удорожить фундамент и подведение коммуникаций."
        ),
    },
    {
        "title": "6. Перспективы района",
        "intro": "Развитие территории влияет на ликвидность и комфорт.",
        "list_title": "Уточните:",
        "items": [
            "планы благоустройства и инфраструктуры",
            "градостроительные ограничения",
            "динамику цен",
        ],
        "closing": (
            "Участок в перспективном районе может вырасти в цене, но и стоить дороже на старте."
        ),
    },
]


class Command(BaseCommand):
    help = "Демо-данные: витрина сайта, FAQ и статьи (повторный запуск безопасен)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-faq",
            action="store_true",
            help="Не создавать записи FAQ",
        )
        parser.add_argument(
            "--skip-articles",
            action="store_true",
            help="Не создавать статьи",
        )
        parser.add_argument(
            "--skip-showcase",
            action="store_true",
            help="Не создавать слайды, преимущества, услуги, команду, отзывы, контакты, заявки",
        )

    def handle(self, *args, **options):
        skip_faq = options["skip_faq"]
        skip_articles = options["skip_articles"]
        skip_showcase = options["skip_showcase"]

        if not skip_faq:
            created_faq = 0
            for sort_order, question, answer in FAQ_SEED:
                _obj, created = FAQEntry.objects.get_or_create(
                    question=question,
                    defaults={
                        "sort_order": sort_order,
                        "answer": answer,
                        "is_active": True,
                    },
                )
                if created:
                    created_faq += 1
            self.stdout.write(
                self.style.SUCCESS(f"FAQ: добавлено новых {created_faq}, всего в базе {FAQEntry.objects.count()}")
            )

        if not skip_showcase:
            _seed_site_contacts(self.stdout, self.style)
            _seed_consultation_leads(self.stdout, self.style)
            _seed_hero_slides(self.stdout, self.style)
            _seed_advantages(self.stdout, self.style)
            _seed_services(self.stdout, self.style)
            _seed_team(self.stdout, self.style)
            _seed_reviews(self.stdout, self.style)

        if skip_articles:
            return

        today = date.today()
        articles_spec = [
            {
                "slug": "na-chto-obratit-vnimanie-pered-pokupkoy-zemli",
                "title": "На что обратить внимание перед покупкой земли",
                "lead": (
                    "Покупка земельного участка — это важный шаг, который требует внимательного "
                    "подхода. Ошибки на этом этапе могут привести к дополнительным расходам, "
                    "юридическим проблемам или ограничениям в строительстве."
                ),
                "description": "Чек-лист: назначение, коммуникации, юридическая чистота и район.",
                "body": (
                    "Вывод: выбор земельного участка — комплексная задача. Совмещайте юридическую "
                    "проверку, инженерные условия и личные приоритеты; при необходимости обратитесь "
                    "к специалистам."
                ),
                "published_at": today,
                "sections": ARTICLE_LAND_SECTIONS,
                "color": (52, 73, 94),
                "image": "demo-article-land.png",
            },
            {
                "slug": "ipoteka-na-nedvizhimost-kak-vybrat-programmu",
                "title": "Ипотека на недвижимость: как выбрать программу",
                "lead": (
                    "Правильный выбор ипотечной программы экономит сотни тысяч рублей. Разбираем "
                    "ключевые параметры, на которые стоит смотреть до визита в банк."
                ),
                "description": "Ставка, взнос, страхование и скрытые платежи простыми словами.",
                "body": (
                    "Итог: сравните несколько предложений по полной стоимости кредита и условиям "
                    "досрочного погашения, а не только по рекламной ставке."
                ),
                "published_at": today - timedelta(days=3),
                "sections": [
                    {
                        "title": "1. Ставка и полная стоимость кредита",
                        "intro": "Номинальная ставка — не единственный показатель.",
                        "list_title": "Обратите внимание:",
                        "items": [
                            "ПСК (полная стоимость кредита) в ключевых документах",
                            "фиксированная или плавающая ставка",
                            "льготные программы и срок их действия",
                        ],
                        "closing": "Попросите у банка расчёт платежей на весь срок с учётом страховок.",
                    },
                    {
                        "title": "2. Первоначальный взнос",
                        "intro": "Чем выше собственные средства, тем ниже риски для банка и часто ставка.",
                        "list_title": "",
                        "items": [],
                        "closing": (
                            "Уточните минимальный взнос по выбранной программе и можно ли включить "
                            "материнский капитал."
                        ),
                    },
                    {
                        "title": "3. Страхование и комиссии",
                        "intro": "Дополнительные продукты могут существенно менять переплату.",
                        "list_title": "Проверьте:",
                        "items": [
                            "страхование жизни и здоровья",
                            "страхование объекта залога",
                            "оформление и сервисные комиссии",
                        ],
                        "closing": "Сравните условия страховщиков — иногда их можно выбрать отдельно.",
                    },
                ],
                "color": (41, 128, 185),
                "image": "demo-article-mortgage.png",
            },
            {
                "slug": "pyat-oshibok-pri-pokupke-kvartiry",
                "title": "5 ошибок при покупке квартиры, которых можно избежать",
                "lead": (
                    "Частые промахи покупателей приводят к срыву сделки, переплате или юридическим "
                    "проблемам. Короткий разбор типичных ситуаций."
                ),
                "description": "Документы, расчёты, осмотр и сроки — что проверить заранее.",
                "body": (
                    "Подготовка и спокойная проверка деталей обычно дешевле, чем исправление "
                    "последствий ошибки после сделки."
                ),
                "published_at": today - timedelta(days=7),
                "sections": [
                    {
                        "title": "1. Не сверили выписку ЕГРН с реальностью",
                        "intro": "",
                        "list_title": "Риски:",
                        "items": ["обременения", "залог", "ограничения на регистрацию"],
                        "closing": "Заказывайте свежую выписку и читайте её с юристом.",
                    },
                    {
                        "title": "2. Поверили только рекламным фото",
                        "intro": "",
                        "list_title": "Что сделать:",
                        "items": ["живой осмотр", "соседей и двор", "шум и инфраструктуру"],
                        "closing": "Дневной и вечерний визит даёт разную картину.",
                    },
                    {
                        "title": "3. Не заложили резерв на налоги и расходы",
                        "intro": "",
                        "list_title": "Учтите:",
                        "items": ["налоги и сборы", "оценка для ипотеки", "ремонт и переезд"],
                        "closing": "Составьте бюджет с запасом 10–15%.",
                    },
                    {
                        "title": "4. Спешка с задатком без условий",
                        "intro": "",
                        "list_title": "",
                        "items": [],
                        "closing": (
                            "Фиксируйте условия возврата/зачёта задатка письменно и проверяйте "
                            "продавца заранее."
                        ),
                    },
                    {
                        "title": "5. Игнорирование сроков банка и регистрации",
                        "intro": "",
                        "list_title": "",
                        "items": [],
                        "closing": (
                            "Согласуйте даты одобрения ипотеки, сделки и подачи на регистрацию "
                            "единым графиком."
                        ),
                    },
                ],
                "color": (142, 68, 173),
                "image": "demo-article-mistakes.png",
            },
            {
                "slug": "novostroyka-ili-vtorichka-plusy-i-minusy",
                "title": "Новостройка или вторичка: плюсы и минусы для покупателя",
                "lead": (
                    "Выбор между новостройкой и вторичным жильём зависит от срока заселения, бюджета "
                    "и вашей готовности к ремонту."
                ),
                "description": "Сравнение по цене, срокам, отделке и рискам.",
                "body": (
                    "Совет: сформулируйте приоритеты (срок, школа, транспорт, планировка) — так "
                    "решение станет проще."
                ),
                "published_at": today - timedelta(days=14),
                "sections": [
                    {
                        "title": "1. Новостройка",
                        "intro": "Свежий фонд и настраиваемая отделка.",
                        "list_title": "Плюсы:",
                        "items": [
                            "новые коммуникации",
                            "гарантия застройщика",
                            "льготная ипотека иногда доступнее",
                        ],
                        "closing": "Минусы: ожидание сдачи, этапы строительства, проверка застройщика.",
                    },
                    {
                        "title": "2. Вторичное жильё",
                        "intro": "Въезд сразу после сделки и развитый район.",
                        "list_title": "Плюсы:",
                        "items": [
                            "видно реальное состояние дома",
                            "знакомая инфраструктура",
                            "торг с продавцом",
                        ],
                        "closing": "Минусы: износ, возможный ремонт, история объекта важнее.",
                    },
                    {
                        "title": "3. Как выбрать",
                        "intro": "",
                        "list_title": "Критерии:",
                        "items": ["срок заселения", "бюджет с ремонтом", "толерантность к риску"],
                        "closing": "Сравните 2–3 варианта в одном ценовом коридоре.",
                    },
                ],
                "color": (39, 174, 96),
                "image": "demo-article-new-vs-old.png",
            },
        ]

        created_articles = 0
        with transaction.atomic():
            for spec in articles_spec:
                art = _create_article(
                    slug=spec["slug"],
                    title=spec["title"],
                    lead=spec["lead"],
                    description=spec["description"],
                    body=spec["body"],
                    published_at=spec["published_at"],
                    sections=spec["sections"],
                    image_color=spec["color"],
                    image_basename=spec["image"],
                )
                if art:
                    created_articles += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Статья: {art.title[:50]}… — slug={spec['slug']}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Статья slug={spec['slug']} уже есть, пропуск.")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Статьи: создано новых {created_articles}, всего {Article.objects.count()}")
        )
