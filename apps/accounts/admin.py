import secrets

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group


from apps.accounts.forms import AgentProfileInlineForm, CreateAgentCabinetForm
from apps.accounts.models import (
    AgentProfile,
    AgentRequest,
    CustomUser,
    District,
    Highway,
    LandPlotListingDetails,
    PropertyCategory,
    ResidentialListingDetails,
    PropertyImage,
    PropertyListing,
    PropertyListingUnit,
    PropertyTag,
)

User = get_user_model()


class AgentProfileInline(admin.StackedInline):
    model = AgentProfile
    form = AgentProfileInlineForm
    can_delete = False
    max_num = 1
    extra = 0
    verbose_name_plural = 'Агент'
    fields = (
        'user_is_verified',
        'issue_password_copy_link',
        'full_name',
        'phone',
        'description',
    )
    readonly_fields = ('issue_password_copy_link',)

    def issue_password_copy_link(self, obj):
        if not obj or not obj.user_id:
            return format_html(
                '<span class="help">После сохранения пользователя здесь будет ссылка на выдачу пароля для копирования.</span>'
            )
        url = reverse('admin:accounts_customuser_issue_password', args=[obj.user_id])
        return format_html(
            '<p class="help">Сохранённый в базе пароль скопировать нельзя (только хеш). '
            'Если забыли выданный пароль — сгенерируйте новый и передайте агенту.</p>'
            '<a class="button" href="{}">Сгенерировать пароль и скопировать</a>',
            url,
        )

    issue_password_copy_link.short_description = 'Пароль для передачи агенту'


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = ('username', 'phone_number', 'is_verified', 'is_staff', 'is_active')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    inlines = (AgentProfileInline,)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('email', 'phone_number')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'phone_number', 'password1', 'password2'),
            },
        ),
    )

    def get_urls(self):
        return [
            path(
                '<path:object_id>/issue-password/',
                self.admin_site.admin_view(self.issue_password_view),
                name='accounts_customuser_issue_password',
            ),
            *super().get_urls(),
        ]

    @staticmethod
    def _new_agent_password():
        for _ in range(12):
            raw = secrets.token_urlsafe(18)
            try:
                validate_password(raw)
                return raw
            except ValidationError:
                continue
        return secrets.token_urlsafe(32)

    def issue_password_view(self, request, object_id):
        user_obj = get_object_or_404(User, pk=object_id)
        context_base = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'user_obj': user_obj,
        }
        if request.method == 'POST':
            plain = self._new_agent_password()
            user_obj.set_password(plain)
            user_obj.save(update_fields=['password'])
            messages.warning(
                request,
                'Пароль изменён. Сохраните или отправьте агенту сейчас — эту страницу повторно открыть с тем же паролем нельзя.',
            )
            return render(
                request,
                'admin/accounts/customuser/issue_password_done.html',
                {
                    **context_base,
                    'plain_password': plain,
                    'title': 'Пароль для копирования',
                },
            )
        return render(
            request,
            'admin/accounts/customuser/issue_password_confirm.html',
            {
                **context_base,
                'title': 'Новый пароль для агента',
            },
        )


@admin.register(AgentRequest)
class AgentRequestAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'status',
        'linked_user',
        'personal_data_consent',
        'created_at',
    )
    list_filter = ('status', 'personal_data_consent', 'created_at')
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at', 'create_cabinet_link', 'status', 'linked_user')

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.linked_user_id:
            ro = list(set(ro + ['name', 'phone', 'personal_data_consent']))
        return ro

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'phone',
                    'personal_data_consent',
                    'status',
                    'linked_user',
                    'create_cabinet_link',
                    'created_at',
                )
            },
        ),
    )

    def create_cabinet_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        if obj.linked_user_id:
            ch = reverse('admin:accounts_customuser_change', args=[obj.linked_user_id])
            pw = reverse('admin:accounts_customuser_issue_password', args=[obj.linked_user_id])
            return format_html(
                '<a class="button" href="{}">Открыть пользователя</a> '
                '<a class="button" href="{}">Новый пароль (копировать)</a>',
                ch,
                pw,
            )
        if obj.status == AgentRequest.Status.NEW:
            url = reverse('admin:accounts_agentrequest_create_cabinet', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Создать личный кабинет</a>',
                url,
            )
        return '—'

    create_cabinet_link.short_description = 'Действия'

    def get_urls(self):
        return [
            path(
                '<path:object_id>/create-cabinet/',
                self.admin_site.admin_view(self.create_cabinet_view),
                name='accounts_agentrequest_create_cabinet',
            ),
            *super().get_urls(),
        ]

    def create_cabinet_view(self, request, object_id):
        req_obj = get_object_or_404(AgentRequest, pk=object_id)
        if req_obj.linked_user_id:
            messages.warning(request, 'Для этой заявки кабинет уже создан.')
            return redirect(reverse('admin:accounts_agentrequest_change', args=[req_obj.pk]))

        if request.method == 'POST':
            form = CreateAgentCabinetForm(request.POST)
            if form.is_valid():
                phone = ' '.join(req_obj.phone.split())
                if User.objects.filter(phone_number=phone).exists():
                    form.add_error(None, 'Пользователь с таким телефоном уже зарегистрирован.')
                else:
                    username = form.cleaned_data['username']
                    password = form.cleaned_data['password1']
                    email_in = (form.cleaned_data.get('email') or '').strip()
                    if email_in:
                        email = email_in
                    else:
                        base = username.replace('@', '_').replace(' ', '_')[:40]
                        email = f'{base}@cabinet.local'
                        n = 0
                        while User.objects.filter(email=email).exists():
                            n += 1
                            email = f'{base}.{n}@cabinet.local'

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        phone_number=phone,
                        is_verified=True,
                        is_active=True,
                    )
                    profile = user.agent_profile
                    profile.full_name = req_obj.name
                    profile.phone = phone
                    profile.save(update_fields=['full_name', 'phone'])
                    req_obj.linked_user = user
                    req_obj.status = AgentRequest.Status.CABINET_CREATED
                    req_obj.save(update_fields=['linked_user', 'status'])
                    messages.success(
                        request,
                        'Кабинет создан. Передайте агенту логин и пароль (при необходимости их можно изменить в карточке пользователя).',
                    )
                    return redirect(reverse('admin:accounts_agentrequest_change', args=[req_obj.pk]))
        else:
            form = CreateAgentCabinetForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'agent_request': req_obj,
            'form': form,
            'title': 'Создать личный кабинет',
        }
        return render(request, 'admin/accounts/agentrequest/create_cabinet.html', context)


class PropertyImageInlineForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ('image', 'sort_order')
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    form = PropertyImageInlineForm
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('image_preview', 'image', 'sort_order')

    @admin.display(description='Превью')
    def image_preview(self, obj):
        if not obj or not obj.pk:
            return '—'
        if not getattr(obj, 'image', None):
            return '—'
        try:
            url = obj.image.url
        except ValueError:
            return '—'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">'
            '<img src="{}" alt="" '
            'style="max-height:140px;max-width:200px;object-fit:contain;vertical-align:middle;'
            'border-radius:4px;border:1px solid #444"/></a>',
            url,
            url,
        )


class PropertyTagInline(admin.TabularInline):
    model = PropertyTag
    extra = 0


class PropertyListingUnitInlineForm(forms.ModelForm):
    class Meta:
        model = PropertyListingUnit
        fields = '__all__'
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PropertyListingUnitInline(admin.TabularInline):
    model = PropertyListingUnit
    form = PropertyListingUnitInlineForm
    extra = 0
    verbose_name = 'Лот (планировка)'
    verbose_name_plural = 'Планировки и цены (лоты ЖК)'
    readonly_fields = ('price_per_sqm',)
    fields = (
        'layout_label',
        'title',
        'building',
        'rooms',
        'is_studio',
        'price',
        'total_area',
        'kitchen_area',
        'floor',
        'floors_total',
        'finishing',
        'price_per_sqm',
        'sort_order',
        'image',
        'completion_text',
        'keys_handover_text',
        'bathroom_summary',
        'ceiling_height',
        'balcony_summary',
        'payment_methods',
        'banks',
        'is_apartments_legal',
        'is_assignment',
        'is_two_level',
        'has_master_bedroom',
    )


class ResidentialListingDetailsInline(admin.StackedInline):
    model = ResidentialListingDetails
    max_num = 1
    extra = 0
    can_delete = True
    verbose_name = 'Жилая (новостройка / вторичка / загород / коттедж / дача)'
    verbose_name_plural = (
        'Блок «жилая недвижимость» (общий для всех категорий, кроме земельного участка)'
    )
    fieldsets = (
        (
            'Как в макете новостройки / ЖК',
            {
                'fields': (
                    'developer',
                    'completion_period_text',
                    'housing_class',
                    'house_construction_type',
                    'parking_info',
                    'registration_settlement',
                    'escrow_bank',
                    'project_finishing',
                    'district_note',
                    'units_total',
                    'units_available',
                    'price_per_sqm_from',
                ),
            },
        ),
        (
            'Договор, оплата, загород (при необходимости)',
            {
                'classes': ('collapse',),
                'fields': (
                    'contract_form',
                    'payment_methods',
                    'travel_time_note',
                    'plot_location_text',
                ),
            },
        ),
    )


class LandPlotListingDetailsInline(admin.StackedInline):
    model = LandPlotListingDetails
    max_num = 1
    extra = 0
    can_delete = True
    fieldsets = (
        (
            'Участок и документы',
            {
                'fields': (
                    'external_reference_id',
                    'plot_number',
                    'cadastral_number',
                    'land_purpose',
                    'contract_form',
                    'completion_quarter_text',
                ),
            },
        ),
    )


_LAND_CATEGORY_SLUG = 'land_plot'


def _detail_inline_class_for_category_slug(slug: str):
    if slug == _LAND_CATEGORY_SLUG:
        return LandPlotListingDetailsInline
    if not slug:
        return None
    return ResidentialListingDetailsInline


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    list_editable = ('sort_order',)
    ordering = ('sort_order', 'name')
    search_fields = ('name', 'slug')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Highway)
class HighwayAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


def _set_property_status(request, queryset, status_value, label_done):
    n = queryset.update(status=status_value)
    messages.success(request, f'{label_done}: {n} шт.')


@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'category',
        'property_type',
        'is_actual_offer',
        'agent',
        'price',
        'status',
        'created_at',
    )
    list_filter = ('status', 'category', 'property_type', 'is_actual_offer', 'created_at')
    list_select_related = ('agent', 'category')
    fieldsets = (
        (
            'Карточка объекта',
            {
                'description': (
                    'Выберите категорию и сохраните. Для «Земельные участки» — блок полей участка; '
                    'для остальных категорий (новостройки, вторичка, загород, коттеджи, дачи, коммерция…) '
                    '— общий блок «жилая недвижимость», как в макете новостройки. Тип объекта (legacy) '
                    'подстраивается от категории.'
                ),
                'fields': (
                    'code',
                    'name',
                    'agent',
                    'category',
                    'property_type',
                    'price',
                    'status',
                    'is_actual_offer',
                    'rejection_reason',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
        ('Описание', {'fields': ('description',)}),
        (
            'Адрес и карта',
            {
                'fields': (
                    'settlement',
                    'district',
                    'highway',
                    'address',
                    'latitude',
                    'longitude',
                    'distance_to_mkad_km',
                ),
            },
        ),
        (
            'Площади и дом',
            {
                'fields': (
                    'area',
                    'land_area',
                    'floors',
                    'rooms',
                    'bedrooms',
                    'bathrooms',
                    'year_built',
                    'wall_material',
                    'finishing',
                ),
            },
        ),
        (
            'Инфраструктура посёлка',
            {
                'classes': ('collapse',),
                'fields': (
                    'has_asphalt_roads',
                    'has_street_lighting',
                    'has_guarded_territory',
                    'near_shops',
                    'near_school_kindergarten',
                    'near_public_transport',
                ),
            },
        ),
        (
            'Коммуникации',
            {
                'fields': (
                    'electricity_supply',
                    'water_supply',
                    'sewage_type',
                    'heating_type',
                    'internet_connection',
                    'communications',
                ),
            },
        ),
    )
    search_fields = (
        'code',
        'name',
        'settlement',
        'address',
        'district__name',
        'highway__name',
        'category__name',
    )
    readonly_fields = ('code', 'created_at', 'updated_at')

    def get_inlines(self, request, obj=None):
        blocks = []
        if obj and obj.category_id:
            slug = getattr(obj.category, 'slug', None)
            if not slug:
                slug = PropertyCategory.objects.filter(pk=obj.category_id).values_list('slug', flat=True).first()
            cls = _detail_inline_class_for_category_slug(slug or '')
            if cls:
                blocks.append(cls)
        return blocks + [PropertyTagInline, PropertyImageInline, PropertyListingUnitInline]
    raw_id_fields = ('agent',)
    actions = (
        'mark_status_published',
        'mark_status_moderation',
        'mark_status_rejected',
    )

    @admin.action(description='Статус: опубликован')
    def mark_status_published(self, request, queryset):
        _set_property_status(
            request,
            queryset,
            PropertyListing.Status.PUBLISHED,
            'Опубликовано',
        )

    @admin.action(description='Статус: на модерации')
    def mark_status_moderation(self, request, queryset):
        _set_property_status(
            request,
            queryset,
            PropertyListing.Status.MODERATION,
            'На модерации',
        )

    @admin.action(description='Статус: отклонён')
    def mark_status_rejected(self, request, queryset):
        _set_property_status(
            request,
            queryset,
            PropertyListing.Status.REJECTED,
            'Отклонено',
        )


admin.site.unregister(Site)
admin.site.unregister(Group)
