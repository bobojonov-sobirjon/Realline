import secrets
import string
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


def property_image_upload_to(instance, filename):
    return f'properties/{instance.property_id}/{filename}'


def listing_unit_image_upload_to(instance, filename):
    return f'listing_units/{instance.listing_id}/{filename}'


class CustomUser(AbstractUser):
    email = models.EmailField(_('email'), unique=True)
    phone_number = models.CharField(_('телефон'), max_length=32, blank=True)
    is_verified = models.BooleanField(
        _('подтверждён администратором'),
        default=False,
        help_text=_(
            'Для входа в API должен быть True. При создании кабинета из заявки выставляется автоматически; '
            'вручную — для пользователей, заведённых только через админку.'
        ),
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')

    def __str__(self):
        return self.username or self.email


class AgentProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        verbose_name=_('пользователь'),
    )
    full_name = models.CharField(_('имя и фамилия'), max_length=255, blank=True)
    phone = models.CharField(_('телефон профиля'), max_length=32, blank=True)
    description = models.TextField(_('описание'), blank=True)

    class Meta:
        verbose_name = _('профиль агента')
        verbose_name_plural = _('профили агентов')

    def __str__(self):
        return self.full_name or self.user.get_username()


class AgentRequest(models.Model):
    """Заявка с сайта: имя и телефон. Кабинет создаётся вручную в админке (логин/пароль)."""

    class Status(models.TextChoices):
        NEW = 'new', _('Новая заявка')
        CABINET_CREATED = 'cabinet_created', _('Кабинет создан')

    name = models.CharField(_('имя'), max_length=255)
    phone = models.CharField(_('телефон'), max_length=32)
    personal_data_consent = models.BooleanField(_('согласие на обработку ПДн'), default=False)
    status = models.CharField(
        _('статус'),
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
    )
    linked_user = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_agent_request',
        verbose_name=_('созданный агент'),
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('заявка агента')
        verbose_name_plural = _('заявки агентов')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.phone}'


class District(models.Model):
    """Справочник районов (Москва и область — демо-данные для каталога)."""

    class Region(models.TextChoices):
        MOSCOW = 'moscow', _('Москва')
        SAINT_PETERSBURG = 'saint_petersburg', _('Санкт-Петербург')

    name = models.CharField(_('название'), max_length=255, unique=True)
    region = models.CharField(
        _('регион'),
        max_length=32,
        choices=Region.choices,
        default=Region.MOSCOW,
        db_index=True,
        help_text=_('Ограничено двумя регионами витрины: Москва или Санкт-Петербург.'),
    )

    class Meta:
        verbose_name = _('район')
        verbose_name_plural = _('районы')
        ordering = ['name']

    def __str__(self):
        return self.name


class Highway(models.Model):
    """Справочник шоссе (демо-данные)."""

    class Region(models.TextChoices):
        MOSCOW = 'moscow', _('Москва')
        SAINT_PETERSBURG = 'saint_petersburg', _('Санкт-Петербург')

    name = models.CharField(_('название'), max_length=255, unique=True)
    region = models.CharField(
        _('регион'),
        max_length=32,
        choices=Region.choices,
        default=Region.MOSCOW,
        db_index=True,
        help_text=_('Ограничено двумя регионами витрины: Москва или Санкт-Петербург.'),
    )

    class Meta:
        verbose_name = _('шоссе')
        verbose_name_plural = _('шоссе')
        ordering = ['name']

    def __str__(self):
        return self.name


class PropertyCategory(models.Model):
    """Категория витрины (новостройки / загород / участок и т.д.)."""

    name = models.CharField(_('название'), max_length=255, unique=True)
    slug = models.SlugField(
        _('код'),
        max_length=64,
        unique=True,
        help_text=_('Латиница без пробелов: new_building, suburban, land_plot…'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)

    class Meta:
        verbose_name = _('категория объекта')
        verbose_name_plural = _('категории объектов')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class PropertyListing(models.Model):
    class PropertyType(models.TextChoices):
        LAND = 'land', _('Земельные участки')
        HOUSE = 'house', _('Дом')
        APARTMENT = 'apartment', _('Квартира')
        COMMERCIAL = 'commercial', _('Коммерческая')
        OTHER = 'other', _('Другое')

    # Категории витрины (кроме land_plot) делят один шаблон карточки и блок «жилая / новостройка»;
    # land_plot — отдельный набор полей.
    _CATEGORY_SLUG_TO_PROPERTY_TYPE = {
        'new_building': PropertyType.APARTMENT,
        'suburban': PropertyType.HOUSE,
        'secondary': PropertyType.APARTMENT,
        'cottage': PropertyType.HOUSE,
        'dacha': PropertyType.HOUSE,
        'land_plot': PropertyType.LAND,
        'commercial': PropertyType.COMMERCIAL,
        'other': PropertyType.OTHER,
    }

    class Status(models.TextChoices):
        MODERATION = 'moderation', _('На модерации')
        PUBLISHED = 'published', _('Опубликован')
        REJECTED = 'rejected', _('Отклонён')

    agent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='property_listings',
        verbose_name=_('агент'),
    )
    code = models.CharField(
        _('код объекта'),
        max_length=32,
        unique=True,
        editable=False,
        blank=True,
        default='',
    )
    property_type = models.CharField(
        _('тип объекта (legacy)'),
        max_length=32,
        choices=PropertyType.choices,
        default=PropertyType.OTHER,
        help_text=_('Подстраивается от категории при сохранении; для фильтров API пока сохраняем.'),
    )
    category = models.ForeignKey(
        PropertyCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name=_('категория витрины'),
        help_text=_(
            'Участок — отдельные поля блока. Остальные категории (новостройки, вторичка, загород, коттеджи, дачи и т.д.) '
            'используют общий блок деталей как в макете новостройки.'
        ),
    )
    name = models.CharField(_('название'), max_length=500)
    price = models.DecimalField(_('цена, ₽'), max_digits=15, decimal_places=2)
    settlement = models.CharField(_('населённый пункт'), max_length=255, blank=True)
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name=_('район'),
    )
    highway = models.ForeignKey(
        Highway,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name=_('шоссе'),
    )
    address = models.CharField(
        _('адрес (улица, дом)'),
        max_length=500,
        blank=True,
        help_text=_('Вручную: улица, дом, ориентир.'),
    )
    area = models.DecimalField(
        _('площадь дома / объекта, м²'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Жилая / общая площадь постройки; для участка без дома можно не заполнять.'),
    )
    land_area = models.DecimalField(
        _('площадь участка, сот.'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Только земля: сотки (1 сотка = 100 м²).'),
    )
    distance_to_mkad_km = models.DecimalField(
        _('до МКАД, км'),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        _('широта (WGS84)'),
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        _('долгота (WGS84)'),
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True,
    )
    has_asphalt_roads = models.BooleanField(_('асфальтированные дороги'), default=False)
    has_street_lighting = models.BooleanField(_('уличное освещение'), default=False)
    has_guarded_territory = models.BooleanField(_('охраняемая территория'), default=False)
    near_shops = models.BooleanField(_('магазины рядом'), default=False)
    near_school_kindergarten = models.BooleanField(_('школа и детский сад рядом'), default=False)
    near_public_transport = models.BooleanField(_('остановка ОТ рядом'), default=False)
    electricity_supply = models.CharField(_('электричество'), max_length=255, blank=True)
    water_supply = models.CharField(_('водоснабжение'), max_length=255, blank=True)
    sewage_type = models.CharField(_('канализация'), max_length=255, blank=True)
    heating_type = models.CharField(_('отопление'), max_length=255, blank=True)
    internet_connection = models.CharField(_('интернет'), max_length=255, blank=True)
    floors = models.PositiveSmallIntegerField(_('этажей'), null=True, blank=True)
    rooms = models.PositiveSmallIntegerField(_('комнат'), null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(_('спален'), null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(_('санузлов'), null=True, blank=True)
    year_built = models.PositiveSmallIntegerField(_('год постройки'), null=True, blank=True)
    wall_material = models.CharField(_('материал стен'), max_length=255, blank=True)
    finishing = models.CharField(_('отделка'), max_length=255, blank=True)
    communications = models.CharField(_('коммуникации'), max_length=500, blank=True)
    description = models.TextField(_('описание'), blank=True)
    status = models.CharField(
        _('статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.MODERATION,
    )
    rejection_reason = models.TextField(_('причина отклонения'), blank=True)
    is_actual_offer = models.BooleanField(
        _('в блоке «Актуальные предложения»'),
        default=False,
        help_text=_('Показ на главной в карусели «Актуальные предложения». Включает администратор.'),
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('объект недвижимости')
        verbose_name_plural = _('объекты недвижимости')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} — {self.name}'

    def save(self, *args, **kwargs):
        if self.category_id:
            slug = (
                PropertyCategory.objects.filter(pk=self.category_id)
                .values_list('slug', flat=True)
                .first()
            )
            if slug:
                pt = self._CATEGORY_SLUG_TO_PROPERTY_TYPE.get(slug)
                if pt is not None:
                    self.property_type = pt
        if not self.code:
            self.code = self._generate_code()
            while True:
                qs = PropertyListing.objects.filter(code=self.code)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                if not qs.exists():
                    break
                self.code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code():
        suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
        return f'RL-{suffix}'


class PropertyListingRejection(models.Model):
    """
    Запись об отклонении объекта модератором: текст для агента, просмотр через API (is_seen).
    Создаётся из админки (кнопка «Отклонить с причиной») или при сохранении карточки со статусом «Отклонён».
    """

    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='rejection_notices',
        verbose_name=_('объект'),
    )
    reason = models.TextField(_('причина отклонения'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    is_seen = models.BooleanField(_('просмотрено агентом'), default=False)
    seen_at = models.DateTimeField(_('когда просмотрено'), null=True, blank=True)

    class Meta:
        verbose_name = _('уведомление об отклонении')
        verbose_name_plural = _('уведомления об отклонении')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.listing.code} @ {self.created_at:%Y-%m-%d %H:%M}'


class ResidentialListingDetails(models.Model):
    """Общий блок карточки для новостроек, вторички, загорода, коттеджей, дач (как в макете ЖК)."""

    listing = models.OneToOneField(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='residential_details',
        verbose_name=_('объект'),
    )
    developer = models.CharField(_('застройщик'), max_length=255, blank=True)
    completion_period_text = models.CharField(
        _('срок сдачи (текст)'),
        max_length=255,
        blank=True,
        help_text=_('Например: 3 кв. 2026 — 2 кв. 2028'),
    )
    housing_class = models.CharField(_('класс жилья'), max_length=128, blank=True)
    house_construction_type = models.CharField(_('тип дома'), max_length=255, blank=True)
    parking_info = models.CharField(_('паркинг'), max_length=255, blank=True)
    registration_settlement = models.CharField(_('регистрация / НП'), max_length=255, blank=True)
    escrow_bank = models.CharField(_('эскроу-счёт (банк)'), max_length=255, blank=True)
    project_finishing = models.CharField(_('отделка (уровень проекта)'), max_length=255, blank=True)
    district_note = models.CharField(_('район (подпись в карточке)'), max_length=255, blank=True)
    units_total = models.PositiveIntegerField(_('всего квартир / единиц'), null=True, blank=True)
    units_available = models.PositiveIntegerField(_('в продаже'), null=True, blank=True)
    price_per_sqm_from = models.DecimalField(
        _('цена за м² от, ₽'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    contract_form = models.CharField(_('форма договора'), max_length=128, blank=True)
    payment_methods = models.TextField(_('способы оплаты'), blank=True)
    travel_time_note = models.CharField(
        _('подпись про дорогу до города'),
        max_length=255,
        blank=True,
        help_text=_('Например: До Москвы — 25 мин на автомобиле'),
    )
    plot_location_text = models.TextField(_('участок и локация (текст)'), blank=True)

    class Meta:
        verbose_name = _('детали: жилая (новостройка / вторичка / загород…)'),
        verbose_name_plural = _('блок «Жилая недвижимость»')

    def __str__(self):
        return f'{self.listing.code}: жилая'


class LandPlotListingDetails(models.Model):
    """Поля карточки «Земельный участок»."""

    listing = models.OneToOneField(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='land_plot_details',
        verbose_name=_('объект'),
    )
    external_reference_id = models.CharField(
        _('ID на витрине'),
        max_length=64,
        blank=True,
        help_text=_('Отображаемый номер для клиента (если нужен).'),
    )
    plot_number = models.CharField(_('№ участка'), max_length=64, blank=True)
    cadastral_number = models.CharField(_('кадастровый номер'), max_length=128, blank=True)
    land_purpose = models.CharField(_('назначение земли'), max_length=255, blank=True)
    contract_form = models.CharField(_('форма договора'), max_length=128, blank=True)
    completion_quarter_text = models.CharField(_('срок сдачи / подключения'), max_length=128, blank=True)

    class Meta:
        verbose_name = _('детали: участок')
        verbose_name_plural = _('блок «Земельный участок»')

    def __str__(self):
        return f'{self.listing.code}: участок'


class PropertyListingUnit(models.Model):
    """
    Квартира / лот внутри ЖК (блок «Планировка и цены»).
    Родитель — PropertyListing; фильтры и сводка — отдельные GET под /catalog/.../units/.
    """

    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name=_('объект-ЖК'),
    )
    layout_label = models.CharField(
        _('группа планировки'),
        max_length=64,
        blank=True,
        help_text=_('Одинаковое значение — одна строка аккордеона (например Студия, 1-комнатная).'),
    )
    title = models.CharField(_('подпись на карточке'), max_length=255, default='', blank=True)
    building = models.CharField(_('корпус'), max_length=64, blank=True)
    completion_text = models.CharField(_('срок сдачи'), max_length=255, blank=True)
    keys_handover_text = models.CharField(_('выдача ключей'), max_length=255, blank=True)
    rooms = models.PositiveSmallIntegerField(_('комнат'), null=True, blank=True)
    is_studio = models.BooleanField(_('студия'), default=False)
    price = models.DecimalField(_('цена, ₽'), max_digits=15, decimal_places=2)
    total_area = models.DecimalField(_('S общая, м²'), max_digits=10, decimal_places=2, null=True, blank=True)
    kitchen_area = models.DecimalField(_('S кухни, м²'), max_digits=10, decimal_places=2, null=True, blank=True)
    floor = models.PositiveSmallIntegerField(_('этаж'), null=True, blank=True)
    floors_total = models.PositiveSmallIntegerField(_('этажей в доме'), null=True, blank=True)
    finishing = models.CharField(_('отделка'), max_length=255, blank=True)
    bathroom_summary = models.CharField(_('санузел'), max_length=255, blank=True)
    ceiling_height = models.CharField(_('высота потолков'), max_length=64, blank=True)
    balcony_summary = models.CharField(_('балкон'), max_length=255, blank=True)
    payment_methods = models.CharField(_('способы оплаты'), max_length=500, blank=True)
    banks = models.CharField(_('банки'), max_length=500, blank=True)
    is_apartments_legal = models.BooleanField(_('апартаменты'), default=False)
    is_assignment = models.BooleanField(_('переуступка'), default=False)
    is_two_level = models.BooleanField(_('двухуровневая'), default=False)
    has_master_bedroom = models.BooleanField(_('мастер-спальня'), default=False)
    price_per_sqm = models.DecimalField(
        _('цена за м², ₽'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    image = models.ImageField(_('планировка / фото'), upload_to=listing_unit_image_upload_to, null=True, blank=True)
    sort_order = models.PositiveIntegerField(_('порядок'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('планировка (лот)')
        verbose_name_plural = _('планировки и цены')
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.listing.code} #{self.pk}'

    def save(self, *args, **kwargs):
        if self.price is not None and self.total_area and self.total_area > 0:
            self.price_per_sqm = (self.price / self.total_area).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class PropertyTag(models.Model):
    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name=_('объект'),
    )
    tag_name = models.CharField(_('тег'), max_length=200)

    class Meta:
        verbose_name = _('тег объекта')
        verbose_name_plural = _('теги объекта')
        ordering = ['id']

    def __str__(self):
        return self.tag_name


class PropertyImage(models.Model):
    property = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('объект'),
    )
    image = models.ImageField(_('изображение'), upload_to=property_image_upload_to)
    sort_order = models.PositiveIntegerField(_('порядок'), default=0)

    class Meta:
        verbose_name = _('изображение объекта')
        verbose_name_plural = _('изображения объектов')
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.property.code} #{self.pk}'


class UserFavoriteListing(models.Model):
    """Избранное: связь пользователь ↔ опубликованный объект (для витрины)."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_listings_links',
        verbose_name=_('пользователь'),
    )
    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='favorited_by_users',
        verbose_name=_('объект'),
    )
    created_at = models.DateTimeField(_('добавлено'), auto_now_add=True)

    class Meta:
        verbose_name = _('избранный объект')
        verbose_name_plural = _('избранное')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=('user', 'listing'), name='unique_user_favorite_listing'),
        ]

    def __str__(self) -> str:
        return f'{self.user_id} → {self.listing_id}'


class UserCompareListing(models.Model):
    """Сравнение объектов (корзина сравнения для авторизованного пользователя)."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='compare_listings_links',
        verbose_name=_('пользователь'),
    )
    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.CASCADE,
        related_name='compared_by_users',
        verbose_name=_('объект'),
    )
    sort_order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    created_at = models.DateTimeField(_('добавлено'), auto_now_add=True)

    class Meta:
        verbose_name = _('объект в сравнении')
        verbose_name_plural = _('сравнение')
        ordering = ['sort_order', 'id']
        constraints = [
            models.UniqueConstraint(fields=('user', 'listing'), name='unique_user_compare_listing'),
        ]

    def __str__(self) -> str:
        return f'{self.user_id} ⇄ {self.listing_id}'
