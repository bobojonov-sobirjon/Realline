import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


def _uf(subdir, _instance, filename):
    return f'website/{subdir}/{uuid.uuid4().hex}_{filename}'


def upload_hero(instance, filename):
    return _uf('hero', instance, filename)


def upload_advantage(instance, filename):
    return _uf('advantages', instance, filename)


def upload_service(instance, filename):
    return _uf('services', instance, filename)


def upload_article(instance, filename):
    return _uf('articles', instance, filename)


def upload_team(instance, filename):
    return _uf('team', instance, filename)


class SiteRegion(models.Model):
    """Город / регион в шапке сайта («Санкт-Петербург»)."""

    name = models.CharField(_('название'), max_length=128)
    slug = models.SlugField(_('slug'), max_length=140, unique=True)
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    latitude = models.DecimalField(
        _('широта (WGS84)'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('Для подбора ближайшего региона по координатам клиента.'),
    )
    longitude = models.DecimalField(
        _('долгота (WGS84)'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('Вместе с широтой — для API геолокации.'),
    )
    is_active = models.BooleanField(_('активен'), default=True)

    class Meta:
        verbose_name = _('регион (город) сайта')
        verbose_name_plural = _('регионы сайта')
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class HeroSlide(models.Model):
    """Слайды / баннеры на главной."""

    title = models.CharField(_('заголовок'), max_length=500)
    subtitle = models.CharField(_('подзаголовок'), max_length=800, blank=True)
    image = models.ImageField(_('изображение'), upload_to=upload_hero)
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    is_active = models.BooleanField(_('показывать'), default=True)

    class Meta:
        verbose_name = _('слайд главной')
        verbose_name_plural = _('слайды главной')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title[:60]


class AdvantageCard(models.Model):
    """«Почему выбирают нас» — карточки преимуществ."""

    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    title = models.CharField(_('заголовок'), max_length=300)
    body = models.TextField(_('текст'))
    image = models.ImageField(_('изображение'), upload_to=upload_advantage, blank=True)
    is_active = models.BooleanField(_('показывать'), default=True)

    class Meta:
        verbose_name = _('преимущество')
        verbose_name_plural = _('преимущества')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title[:50]


class ServiceCard(models.Model):
    """Услуга: карточка на главном блоке + полная страница (лендинг)."""

    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    title = models.CharField(_('заголовок'), max_length=300)
    slug = models.SlugField(
        _('slug'),
        max_length=320,
        unique=True,
        null=True,
        blank=True,
        allow_unicode=True,
        help_text=_('Опционально, для URL; запросы работают по `id`. Несколько пустых значений допустимы только с NULL.'),
    )
    body = models.TextField(
        _('краткое описание (карточка)'),
        help_text=_('Текст для плитки «Другие услуги» / списка на главной.'),
    )
    hero_text = models.TextField(
        _('текст героя (страница услуги)'),
        blank=True,
        help_text=_('Основной текст под заголовком на странице услуги (несколько абзацев).'),
    )
    image = models.ImageField(_('изображение (герой / карточка)'), upload_to=upload_service)
    section_features_title = models.CharField(
        _('заголовок блока «Что вы получите»'),
        max_length=200,
        default='Что вы получите',
        blank=True,
    )
    section_workflow_title = models.CharField(
        _('заголовок блока «Как мы работаем»'),
        max_length=200,
        default='Как мы работаем',
        blank=True,
    )
    cta_label = models.CharField(
        _('текст кнопки заявки'),
        max_length=120,
        default='Оставить заявку',
        blank=True,
    )
    related_services = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='related_from',
        verbose_name=_('другие услуги (внизу страницы)'),
    )
    is_active = models.BooleanField(_('показывать'), default=True)

    class Meta:
        verbose_name = _('услуга')
        verbose_name_plural = _('услуги')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title[:50]


class ServiceFeatureLine(models.Model):
    service = models.ForeignKey(
        ServiceCard,
        on_delete=models.CASCADE,
        related_name='feature_lines',
        verbose_name=_('услуга'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    text = models.CharField(_('пункт списка'), max_length=600)

    class Meta:
        verbose_name = _('пункт «Что вы получите»')
        verbose_name_plural = _('пункты «Что вы получите»')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.text[:48]


class ServicePillTag(models.Model):
    service = models.ForeignKey(
        ServiceCard,
        on_delete=models.CASCADE,
        related_name='pill_tags',
        verbose_name=_('услуга'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    text = models.CharField(_('тег-чип'), max_length=200)

    class Meta:
        verbose_name = _('чип под блоком преимуществ')
        verbose_name_plural = _('чипы')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.text[:40]


class ServiceBenefitBlock(models.Model):
    service = models.ForeignKey(
        ServiceCard,
        on_delete=models.CASCADE,
        related_name='benefit_blocks',
        verbose_name=_('услуга'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    title = models.CharField(_('заголовок'), max_length=300)
    body = models.TextField(_('описание'))

    class Meta:
        verbose_name = _('блок выгоды (оранжевая карточка)')
        verbose_name_plural = _('блоки выгод')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title[:40]


class ServiceWorkflowStep(models.Model):
    service = models.ForeignKey(
        ServiceCard,
        on_delete=models.CASCADE,
        related_name='workflow_steps',
        verbose_name=_('услуга'),
    )
    step_number = models.PositiveSmallIntegerField(_('номер шага'), default=1)
    title = models.CharField(_('заголовок шага'), max_length=300)
    body = models.TextField(_('подзаголовок / описание'), blank=True)

    class Meta:
        verbose_name = _('шаг «Как мы работаем»')
        verbose_name_plural = _('шаги процесса')
        ordering = ['step_number', 'id']

    def __str__(self) -> str:
        return f'{self.step_number}. {self.title[:30]}'


class FAQEntry(models.Model):
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    question = models.CharField(_('вопрос'), max_length=500)
    answer = models.TextField(_('ответ'))
    is_active = models.BooleanField(_('показывать'), default=True)

    class Meta:
        verbose_name = _('вопрос FAQ')
        verbose_name_plural = _('FAQ')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.question[:60]


class Article(models.Model):
    slug = models.SlugField(_('slug'), max_length=220, unique=True, allow_unicode=True)
    title = models.CharField(_('заголовок'), max_length=500)
    lead = models.CharField(_('подзаголовок / лид'), max_length=600, blank=True)
    description = models.TextField(
        _('краткое описание'),
        blank=True,
        help_text=_('Анонс для карточек, meta/snippet; отличается от короткого лида под заголовком.'),
    )
    image = models.ImageField(_('обложка'), upload_to=upload_article)
    published_at = models.DateField(_('дата публикации'))
    body = models.TextField(
        _('legacy: текст/HTML целиком'),
        blank=True,
        help_text=_('Старый формат одного поля; для новых статей используйте блоки ниже (inline в админке).'),
    )
    is_published = models.BooleanField(_('опубликовано'), default=True)

    class Meta:
        verbose_name = _('статья блога')
        verbose_name_plural = _('статьи блога')
        ordering = ['-published_at', '-id']

    def __str__(self) -> str:
        return self.title[:60]


class ArticleSection(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='content_sections',
        verbose_name=_('статья'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок блока'), default=0)
    title = models.CharField(_('заголовок блока'), max_length=500)
    intro = models.TextField(_('вводный текст'), blank=True)
    list_title = models.CharField(_('заголовок списка'), max_length=500, blank=True)
    closing = models.TextField(_('текст после списка'), blank=True)

    class Meta:
        verbose_name = _('блок статьи')
        verbose_name_plural = _('блоки статьи')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.title[:60]


class ArticleSectionItem(models.Model):
    section = models.ForeignKey(
        ArticleSection,
        on_delete=models.CASCADE,
        related_name='list_items',
        verbose_name=_('блок'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок пункта'), default=0)
    text = models.CharField(_('текст пункта списка'), max_length=1000)

    class Meta:
        verbose_name = _('пункт списка')
        verbose_name_plural = _('пункты списка')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.text[:60]


class TeamMember(models.Model):
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    full_name = models.CharField(_('ФИО'), max_length=200)
    role = models.CharField(_('должность'), max_length=200)
    experience = models.CharField(_('опыт'), max_length=300, blank=True)
    photo = models.ImageField(_('фото'), upload_to=upload_team)
    is_active = models.BooleanField(_('показывать'), default=True)

    class Meta:
        verbose_name = _('сотрудник')
        verbose_name_plural = _('команда')
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.full_name


class ClientReview(models.Model):
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    author_name = models.CharField(_('автор'), max_length=200)
    city = models.CharField(_('город'), max_length=200, blank=True)
    text = models.TextField(_('текст отзыва'))
    is_published = models.BooleanField(_('опубликовано'), default=True)

    class Meta:
        verbose_name = _('отзыв клиента')
        verbose_name_plural = _('отзывы клиентов')
        ordering = ['sort_order', '-id']

    def __str__(self) -> str:
        return f'{self.author_name}'


class SiteContacts(models.Model):
    """Одна запись: контакты компании (редактировать в админке п. 1)."""

    phone = models.CharField(_('телефон'), max_length=64)
    email = models.EmailField(_('email'))
    address = models.CharField(_('адрес офиса'), max_length=500)
    work_hours = models.CharField(
        _('режим работы'),
        max_length=300,
        help_text=_('Напр.: Пн–Пт 9:00–18:00; Сб–Вс — выходной'),
    )
    telegram_url = models.URLField(_('Telegram'), blank=True)
    vk_url = models.URLField(_('ВКонтакте'), blank=True)
    map_embed_url = models.URLField(
        _('URL карты (iframe / ссылка)'),
        max_length=800,
        blank=True,
        help_text=_('Опционально: ссылка на Яндекс.Карты / Google Maps'),
    )

    class Meta:
        verbose_name = _('контакты сайта')
        verbose_name_plural = _('контакты сайта')

    def __str__(self) -> str:
        return str(_('Контакты компании'))


class ConsultationLead(models.Model):
    """Заявка «Получить консультацию» с публичного сайта."""

    name = models.CharField(_('имя'), max_length=255)
    phone = models.CharField(_('телефон'), max_length=32)
    email = models.EmailField(_('email'), blank=True)
    message = models.TextField(_('комментарий'), blank=True)
    personal_data_consent = models.BooleanField(_('согласие на обработку ПДн'), default=False)
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('заявка на консультацию')
        verbose_name_plural = _('заявки на консультацию')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} — {self.phone}'
