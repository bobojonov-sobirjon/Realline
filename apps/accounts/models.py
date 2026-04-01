import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


def property_image_upload_to(instance, filename):
    return f'properties/{instance.property_id}/{filename}'


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

    name = models.CharField(_('название'), max_length=255, unique=True)

    class Meta:
        verbose_name = _('район')
        verbose_name_plural = _('районы')
        ordering = ['name']

    def __str__(self):
        return self.name


class Highway(models.Model):
    """Справочник шоссе (демо-данные)."""

    name = models.CharField(_('название'), max_length=255, unique=True)

    class Meta:
        verbose_name = _('шоссе')
        verbose_name_plural = _('шоссе')
        ordering = ['name']

    def __str__(self):
        return self.name


class PropertyListing(models.Model):
    class PropertyType(models.TextChoices):
        LAND = 'land', _('Земельные участки')
        HOUSE = 'house', _('Дом')
        APARTMENT = 'apartment', _('Квартира')
        COMMERCIAL = 'commercial', _('Коммерческая')
        OTHER = 'other', _('Другое')

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
        _('тип объекта'),
        max_length=32,
        choices=PropertyType.choices,
        default=PropertyType.OTHER,
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
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        _('долгота (WGS84)'),
        max_digits=9,
        decimal_places=6,
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
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('объект недвижимости')
        verbose_name_plural = _('объекты недвижимости')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} — {self.name}'

    def save(self, *args, **kwargs):
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
