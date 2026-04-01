import os
from datetime import timedelta
from pathlib import Path


# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_dotenv = None
    
    
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)j=0^e5+w2m@39mv5oyr4kw!*8x)0823koc81t45!#h2dz^q9c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Обратное геокодирование (GET /api/v1/site/geo/?lat=&lon=) — политика Nominatim требует осмысленный User-Agent.
NOMINATIM_USER_AGENT = os.getenv(
    'NOMINATIM_USER_AGENT',
    'RealEstateRus/1.0 (contact: set NOMINATIM_USER_AGENT in .env)',
)


# Application definition

LOCAL_APPS = [
    'apps.accounts',
    'apps.website',
]

INSTALLED_APPS = [
    'django.contrib.sites',
    'jazzmin',
    'nested_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'django_filters',
    *LOCAL_APPS,
]

LOCAL_MIDDLEWARE = [
    'config.middleware.middleware.JsonErrorResponseMiddleware',
    'config.middleware.middleware.Custom404Middleware',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    *LOCAL_MIDDLEWARE,
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'real_estate'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '0576'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = "/media/"
# Production uchun /var/www/media, development uchun local media folder
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/media')


LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    "PAGE_SIZE": 100,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']

# CORS Headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

# CORS Methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# CSRF Settings for production
CSRF_COOKIE_SECURE = False  # Set True if using HTTPS
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'

# Session Settings
SESSION_COOKIE_SECURE = False  # Set True if using HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# Security Settings for development/production
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'accounts.CustomUser'

SITE_ID = 1

# django-jazzmin — https://django-jazzmin.readthedocs.io/
JAZZMIN_SETTINGS = {
    'site_title': 'RealEstateRus Admin',
    'site_header': 'RealEstateRus',
    'site_brand': 'RealEstateRus',
    'welcome_sign': 'RealEstateRus — администрирование',
    'copyright': 'RealEstateRus',
    'search_model': ['accounts.CustomUser', 'auth.Group'],
    'user_avatar': None,
    'topmenu_links': [
        {'name': 'Admin home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'API docs', 'url': '/docs/', 'new_window': True},
    ],
    'show_sidebar': True,
    # Приложения accounts и website скрыты — иначе Jazzmin дублирует те же модели с custom_links.
    'navigation_expanded': True,
    'hide_apps': ['accounts', 'website'],
    'hide_models': [],
    # Ключи в нижнем регистре — так Jazzmin находит иконки (см. get_settings: icons в lower).
    'custom_links': {
        'Агенты — пользователи и заявки': [
            {
                'name': 'Пользователи (агенты)',
                'url': 'admin:accounts_customuser_changelist',
                'icon': 'fas fa-user',
                'permissions': ['accounts.view_customuser'],
            },
            {
                'name': 'Заявки агентов',
                'url': 'admin:accounts_agentrequest_changelist',
                'icon': 'fas fa-inbox',
                'permissions': ['accounts.view_agentrequest'],
            },
        ],
        'Объекты и каталог': [
            {
                'name': 'Объекты недвижимости',
                'url': 'admin:accounts_propertylisting_changelist',
                'icon': 'fas fa-city',
                'permissions': ['accounts.view_propertylisting'],
            },
            {
                'name': 'Районы',
                'url': 'admin:accounts_district_changelist',
                'icon': 'fas fa-map-marked-alt',
                'permissions': ['accounts.view_district'],
            },
            {
                'name': 'Шоссе',
                'url': 'admin:accounts_highway_changelist',
                'icon': 'fas fa-road',
                'permissions': ['accounts.view_highway'],
            },
        ],
        'Сайт — витрина': [
            {
                'name': 'Регионы / города',
                'url': 'admin:website_siteregion_changelist',
                'icon': 'fas fa-map-pin',
                'permissions': ['website.view_siteregion'],
            },
            {
                'name': 'Слайды главной',
                'url': 'admin:website_heroslide_changelist',
                'icon': 'fas fa-images',
                'permissions': ['website.view_heroslide'],
            },
            {
                'name': 'Преимущества',
                'url': 'admin:website_advantagecard_changelist',
                'icon': 'fas fa-star',
                'permissions': ['website.view_advantagecard'],
            },
            {
                'name': 'Услуги',
                'url': 'admin:website_servicecard_changelist',
                'icon': 'fas fa-concierge-bell',
                'permissions': ['website.view_servicecard'],
            },
            {
                'name': 'FAQ',
                'url': 'admin:website_faqentry_changelist',
                'icon': 'fas fa-question-circle',
                'permissions': ['website.view_faqentry'],
            },
            {
                'name': 'Статьи блога',
                'url': 'admin:website_article_changelist',
                'icon': 'fas fa-blog',
                'permissions': ['website.view_article'],
            },
            {
                'name': 'Команда',
                'url': 'admin:website_teammember_changelist',
                'icon': 'fas fa-users',
                'permissions': ['website.view_teammember'],
            },
            {
                'name': 'Отзывы',
                'url': 'admin:website_clientreview_changelist',
                'icon': 'fas fa-comment-dots',
                'permissions': ['website.view_clientreview'],
            },
            {
                'name': 'Контакты компании',
                'url': 'admin:website_sitecontacts_changelist',
                'icon': 'fas fa-address-book',
                'permissions': ['website.view_sitecontacts'],
            },
            {
                'name': 'Заявки на консультацию',
                'url': 'admin:website_consultationlead_changelist',
                'icon': 'fas fa-inbox',
                'permissions': ['website.view_consultationlead'],
            },
        ],
    },
    'order_with_respect_to': [
        'auth',
        'агенты — пользователи и заявки',
        'объекты и каталог',
        'сайт — витрина',
        'sites',
    ],
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'accounts': 'fas fa-user-tie',
        'accounts.customuser': 'fas fa-user',
        'accounts.agentrequest': 'fas fa-inbox',
        'агенты — пользователи и заявки': 'fas fa-user-tie',
        'объекты и каталог': 'fas fa-th-large',
        'сайт — витрина': 'fas fa-store',
        'sites': 'fas fa-globe',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',
    'related_modal_active': False,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'auth.user': 'collapsible',
        'auth.group': 'vertical_tabs',
    },
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-dark',
    'accent': 'accent-teal',
    'navbar': 'navbar-dark',
    'navbar_fixed': False,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Change to your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sobirbobojonov2000@gmail.com'
EMAIL_HOST_PASSWORD = 'harntaefuxuvlqqw'
DEFAULT_FROM_EMAIL = 'sobirbobojonov2000@gmail.com'


# DRF Spectacular Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Realline / RealEstateRus API',
    'DESCRIPTION': (
        'REST API для агентов, публичного каталога и **контента сайта** (витрина). '
        'JWT (Bearer) для кабинета агента, избранного и сравнения. '
        'Эндпоинты **`/api/v1/site/`** — публично (GET), кроме POST заявки на консультацию.'
    ),
    'VERSION': 'v1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'SWAGGER_UI_FAVICON_HREF': '/static/favicon.ico',
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': True,
        'hideHostname': True,
    },
    'SERVERS': [
        {'url': 'https://85.198.101.179:8005', 'description': 'Production server'},
        {'url': 'http://localhost:8000', 'description': 'Development server'},
    ],
    'TAGS': [
        {
            'name': 'Accounts — авторизация',
            'description': 'POST /register/ (заявка с формы), POST /login/, POST /token/refresh/ — JWT.',
        },
        {'name': 'Accounts — профиль', 'description': 'Профиль агента и смена пароля'},
        {
            'name': 'Accounts — объекты',
            'description': 'Объекты агента: GET/POST список, GET/PUT/PATCH/DELETE карточка; POST multipart/form-data или JSON.',
        },
        {
            'name': 'Каталог',
            'description': 'Справочники районов и шоссе (GET), публичный список объектов с фильтрами.',
        },
        {
            'name': 'Сайт — регионы',
            'description': (
                'Города РФ в админке/сидах. GET /api/v1/site/regions/?name=… '
                'GET /api/v1/site/geo/ — place_name по lat/lon (OSM Nominatim) или демо по IP.'
            ),
        },
        {
            'name': 'Сайт — баннеры',
            'description': 'Слайды главной страницы. GET /api/v1/site/hero-slides/',
        },
        {
            'name': 'Сайт — преимущества',
            'description': 'Карточки «Почему мы». GET /api/v1/site/advantages/',
        },
        {
            'name': 'Сайт — услуги',
            'description': 'Список карточек GET /api/v1/site/services/; полная страница услуги GET /api/v1/site/services/{id}/.',
        },
        {
            'name': 'Сайт — FAQ',
            'description': 'Частые вопросы и ответы. GET /api/v1/site/faq/',
        },
        {
            'name': 'Сайт — блог',
            'description': 'Статьи: список и деталь по slug. GET /api/v1/site/articles/',
        },
        {
            'name': 'Сайт — команда',
            'description': 'Сотрудники. GET /api/v1/site/team/',
        },
        {
            'name': 'Сайт — отзывы',
            'description': 'Отзывы клиентов. GET /api/v1/site/reviews/',
        },
        {
            'name': 'Сайт — контакты',
            'description': 'Телефон, email, адрес, соцсети. GET /api/v1/site/contacts/',
        },
        {
            'name': 'Сайт — консультации',
            'description': 'Заявка с формы «Получить консультацию». POST /api/v1/site/consultation/ без JWT.',
        },
        {
            'name': 'Accounts — витрина (пользователь)',
            'description': 'Избранное и сравнение для **авторизованного** пользователя (JWT). Только опубликованные объекты из каталога.',
        },
    ],
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
    'GENERIC_ADDITIONAL_PROPERTIES': None,
    'CAMPAIGN': None,
    'CONTACT': {
        'name': 'API Support',
        'email': 'contact@snippets.local',
    },
    'LICENSE': {
        'name': 'BSD License',
    },
}