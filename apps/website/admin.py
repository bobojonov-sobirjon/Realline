import nested_admin
from django.contrib import admin

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
    SiteRegion,
    TeamMember,
)


@admin.register(SiteRegion)
class SiteRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'latitude', 'longitude', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'site_region', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active', 'site_region')


@admin.register(AdvantageCard)
class AdvantageCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')


class ServiceFeatureLineInline(admin.TabularInline):
    model = ServiceFeatureLine
    extra = 0


class ServicePillTagInline(admin.TabularInline):
    model = ServicePillTag
    extra = 0


class ServiceBenefitBlockInline(admin.TabularInline):
    model = ServiceBenefitBlock
    extra = 0


class ServiceWorkflowStepInline(admin.TabularInline):
    model = ServiceWorkflowStep
    extra = 0


@admin.register(ServiceCard)
class ServiceCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_services',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'related_services':
            qs = ServiceCard.objects.filter(is_active=True).order_by('sort_order', 'title')
            oid = request.resolver_match.kwargs.get('object_id') if request.resolver_match else None
            if oid:
                qs = qs.exclude(pk=oid)
            kwargs['queryset'] = qs
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    fieldsets = (
        (None, {'fields': ('title', 'slug', 'sort_order', 'is_active')}),
        ('Карточка в списке', {'fields': ('body', 'image')}),
        (
            'Страница услуги',
            {
                'fields': (
                    'hero_text',
                    'section_features_title',
                    'section_workflow_title',
                    'cta_label',
                ),
            },
        ),
        ('Другие услуги (внизу)', {'fields': ('related_services',)}),
    )
    inlines = (
        ServiceFeatureLineInline,
        ServicePillTagInline,
        ServiceBenefitBlockInline,
        ServiceWorkflowStepInline,
    )


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ('question', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')


class ArticleSectionItemInline(nested_admin.NestedTabularInline):
    model = ArticleSectionItem
    extra = 0
    sortable_field_name = 'sort_order'
    fields = ('sort_order', 'text')


class ArticleSectionInline(nested_admin.NestedStackedInline):
    model = ArticleSection
    extra = 0
    sortable_field_name = 'sort_order'
    fields = ('sort_order', 'title', 'intro', 'list_title', 'closing')
    inlines = (ArticleSectionItemInline,)


@admin.register(Article)
class ArticleAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'slug', 'published_at', 'is_published')
    list_filter = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug', 'description')
    inlines = (ArticleSectionInline,)
    fieldsets = (
        (
            None,
            {
                'fields': ('title', 'slug', 'lead', 'description', 'image', 'published_at', 'is_published'),
                'description': (
                    'Блоки статьи (title, intro, список и т.д.) — кнопкой «Добавить ещё один Блок статьи» ниже. '
                    'Пункты списка — «+ Добавить ещё один Пункт списка» во вложенной таблице. '
                    'Формат API: см. apps/website/article_sections.py.'
                ),
            },
        ),
        ('Устаревшее одно поле', {'fields': ('body',), 'classes': ('collapse',)}),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')


@admin.register(ClientReview)
class ClientReviewAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'city', 'sort_order', 'is_published')
    list_editable = ('sort_order', 'is_published')


@admin.register(SiteContacts)
class SiteContactsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteContacts.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConsultationLead)
class ConsultationLeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'personal_data_consent', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    search_fields = ('name', 'phone', 'email')
