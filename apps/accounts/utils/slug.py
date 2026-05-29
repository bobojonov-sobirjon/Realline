"""Генерация slug для объектов каталога (латиница из кириллицы)."""

from django.utils.text import slugify

_CYRILLIC_TO_LATIN = {
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'е': 'e',
    'ё': 'e',
    'ж': 'zh',
    'з': 'z',
    'и': 'i',
    'й': 'y',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'х': 'h',
    'ц': 'ts',
    'ч': 'ch',
    'ш': 'sh',
    'щ': 'sch',
    'ъ': '',
    'ы': 'y',
    'ь': '',
    'э': 'e',
    'ю': 'yu',
    'я': 'ya',
}


def transliterate_ru(text: str) -> str:
    out = []
    for ch in (text or '').lower():
        if ch in _CYRILLIC_TO_LATIN:
            out.append(_CYRILLIC_TO_LATIN[ch])
        else:
            out.append(ch)
    return ''.join(out)


def slug_base_from_listing_name(name: str, code: str = '') -> str:
    base = slugify(transliterate_ru(name or ''))[:50].strip('-')
    if not base and code:
        base = slugify(transliterate_ru(code))[:50].strip('-')
    if not base:
        base = 'listing'
    return base


def generate_unique_listing_slug(model_cls, name: str, code: str = '', exclude_pk=None) -> str:
    import secrets

    base = slug_base_from_listing_name(name, code)
    candidate = base
    n = 0
    qs = model_cls.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=candidate).exists():
        n += 1
        candidate = f'{base}-{n}'
        if n > 50:
            candidate = f'{base}-{secrets.token_hex(3)}'
            break
    return candidate
