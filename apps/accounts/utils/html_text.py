"""Очистка HTML-описаний объектов для читабельного текста на витрине."""

from __future__ import annotations

import html
import re

from django.utils.html import strip_tags

_BLOCK_END = re.compile(r'</(p|div|li|h[1-6]|tr|blockquote)>', re.IGNORECASE)
_BR = re.compile(r'<br\s*/?>', re.IGNORECASE)
_MULTI_SPACE = re.compile(r'[ \t]{2,}')
_MULTI_NEWLINE = re.compile(r'\n{3,}')


def clean_listing_description(raw: str | None) -> str:
    """
    Убирает теги (<p>, <a>…), декодирует сущности (&laquo;, &nbsp;, &mdash;).
    Сохраняет абзацы переносами строк.
    """
    if not raw:
        return ''

    text = str(raw)
    text = _BR.sub('\n', text)
    text = _BLOCK_END.sub('\n\n', text)
    text = strip_tags(text)
    text = html.unescape(text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = _MULTI_NEWLINE.sub('\n\n', text)
    text = _MULTI_SPACE.sub(' ', text)
    return text.strip()
