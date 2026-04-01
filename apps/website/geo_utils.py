"""Геолокация: обратное геокодирование (OSM Nominatim), демо по IP, расстояния."""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional, Tuple

from django.conf import settings


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя точками на сфере, км (WGS84)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return (request.META.get('REMOTE_ADDR') or '').strip() or '0.0.0.0'


def reverse_geocode_osm(lat: float, lon: float, timeout: float = 4.0) -> Optional[dict]:
    """
    Название места по координатам (OpenStreetMap Nominatim).
    См. https://operations.osmfoundation.org/policies/nominatim/ — нужен свой User-Agent.
    """
    ua = getattr(
        settings,
        'NOMINATIM_USER_AGENT',
        'RealEstateRus/1.0 (https://github.com/; contact: admin@local)',
    )
    q = urllib.parse.urlencode(
        {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 14,
            'accept-language': 'ru,en,uz',
        }
    )
    url = f'https://nominatim.openstreetmap.org/reverse?{q}'
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return None

    addr = data.get('address') or {}
    place = (
        addr.get('city')
        or addr.get('town')
        or addr.get('village')
        or addr.get('hamlet')
        or addr.get('municipality')
        or addr.get('county')
        or addr.get('state')
        or data.get('name')
        or ''
    )
    display = (data.get('display_name') or '').strip()
    if not place and display:
        place = display.split(',')[0].strip()
    return {
        'place_name': place or None,
        'full_address': display or None,
        'country': addr.get('country'),
        'country_code': (addr.get('country_code') or '').upper() or None,
    }


def fake_ip_geolocation_demo(ip: str) -> dict:
    """
    Демо-данные «по IP» без внешнего GeoIP-провайдера.
    Город выбирается детерминированно по строке IP для разнообразия в тестах.
    """
    cities = [
        ('Москва', 'Центральный федеральный округ', 55.7558, 37.6176),
        ('Санкт-Петербург', 'Северо-Западный федеральный округ', 59.9343, 30.3351),
        ('Казань', 'Приволжский федеральный округ', 55.7963, 49.1088),
        ('Новосибирск', 'Сибирский федеральный округ', 55.0084, 82.9357),
        ('Екатеринбург', 'Уральский федеральный округ', 56.8431, 60.6454),
        ('Краснодар', 'Южный федеральный округ', 45.0355, 38.9753),
        ('Владивосток', 'Дальневосточный федеральный округ', 43.1155, 131.8855),
        ('Калининград', 'Северо-Западный федеральный округ', 54.7104, 20.4522),
    ]
    h = sum(ord(c) for c in ip) if ip else 0
    city, fed, lat, lon = cities[h % len(cities)]
    return {
        'country_code': 'RU',
        'country_name': 'Россия',
        'city_name': city,
        'region_name': fed,
        'latitude': lat,
        'longitude': lon,
        'demo': True,
        'demo_note': 'Без внешнего GeoIP: город выбран по хешу IP для демонстрации.',
    }


def nearest_region_with_coords(regions_qs, lat: float, lon: float) -> Tuple[Optional[Any], Optional[float]]:
    """Оставлено для возможного использования (подбор города из справочника сайта)."""
    best = None
    best_km = None
    for r in regions_qs.filter(latitude__isnull=False, longitude__isnull=False):
        d = haversine_km(lat, lon, float(r.latitude), float(r.longitude))
        if best_km is None or d < best_km:
            best_km = d
            best = r
    return best, best_km
