"""Импорт data/trendagent_export/ → PropertyListing + units + images."""

from __future__ import annotations

import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import transaction

from apps.accounts.models import (
    District,
    PropertyCategory,
    PropertyImage,
    PropertyListing,
    PropertyListingUnit,
    ResidentialListingDetails,
)
from apps.accounts.utils.html_text import clean_listing_description
from apps.accounts.utils.region import normalize_listing_region

User = get_user_model()

SETTLEMENT_BY_REGION = {
    District.Region.MOSCOW: 'Москва',
    District.Region.SAINT_PETERSBURG: 'Санкт-Петербург',
}


def resolve_export_region(summary: dict, complex_dir: Path) -> str:
    """Регион витрины: moscow | saint_petersburg (District.Region)."""
    for raw in (
        summary.get('region'),
        summary.get('folder'),
        complex_dir.parent.name,
    ):
        hit = normalize_listing_region(raw)
        if hit:
            return hit
    return District.Region.MOSCOW


def _decimal(value) -> Decimal | None:
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _format_deadline(value: str | None) -> str:
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        quarter = (dt.month - 1) // 3 + 1
        return f'{quarter} кв. {dt.year}'
    except (ValueError, TypeError):
        return str(value)[:32]


def _parse_rooms(apt: dict) -> tuple[int | None, bool, str]:
    label = (apt.get('rooms') or '').strip()
    if apt.get('is_studio') or 'студ' in label.lower():
        return 0, True, label or 'Студия'
    match = re.search(r'(\d+)', label)
    if match:
        return int(match.group(1)), False, label
    return None, False, label


def _unit_title(apt: dict) -> str:
    parts: list[str] = []
    if apt.get('number'):
        parts.append(f'№{apt["number"]}')
    if apt.get('building'):
        parts.append(f'корп. {apt["building"]}')
    if apt.get('floor') is not None:
        parts.append(f'{apt["floor"]} этаж')
    return ', '.join(parts) or (apt.get('block_name') or 'Лот')


def _resolve_district(region: str, district_label: str) -> District | None:
    if not district_label:
        return None
    label = (
        district_label.replace(' р-н', '')
        .replace(' район', '')
        .replace('(СПб)', '')
        .strip()
    )
    qs = District.objects.filter(region=region)
    hit = qs.filter(name__iexact=label).first()
    if hit:
        return hit
    hit = qs.filter(name__icontains=label).first()
    if hit:
        return hit
    for cand in qs:
        cn = cand.name.lower()
        ln = label.lower()
        if cn in ln or ln in cn:
            return cand
    return None


def _subway_note(subways: list[dict]) -> str:
    parts: list[str] = []
    for item in subways or []:
        name = item.get('name')
        minutes = item.get('minutes')
        if not name or not minutes:
            continue
        mode = 'пешком' if item.get('type') == 1 else 'транспортом'
        parts.append(f'{name} — {minutes} мин {mode}')
    return '; '.join(parts)


def _ensure_category() -> PropertyCategory:
    cat, _ = PropertyCategory.objects.get_or_create(
        slug='new_building',
        defaults={'name': 'Новостройки', 'sort_order': 1},
    )
    return cat


def _ensure_agent(username: str | None = None):
    if username:
        user = User.objects.filter(username=username).first()
        if user:
            return user
        raise ValueError(f'Пользователь {username!r} не найден.')
    user = User.objects.filter(is_superuser=True).first()
    if user:
        return user
    user = User.objects.filter(is_verified=True).first()
    if user:
        return user
    return User.objects.create_user(
        username='trendagent_import',
        email='trendagent_import@local.invalid',
        password='TrendAgentImport2026!',
        is_verified=True,
        is_staff=True,
    )


def iter_export_complexes(
    export_root: Path,
    *,
    region: str | None = None,
    guid: str | None = None,
):
    if not export_root.is_dir():
        return
    for region_dir in sorted(export_root.iterdir()):
        if not region_dir.is_dir():
            continue
        for complex_dir in sorted(region_dir.iterdir()):
            summary_path = complex_dir / 'summary.json'
            if not summary_path.is_file():
                continue
            summary = json.loads(summary_path.read_text(encoding='utf-8'))
            item_region = resolve_export_region(summary, complex_dir)
            item_guid = (summary.get('guid') or complex_dir.name).lower()
            if region:
                filter_region = normalize_listing_region(region)
                if filter_region and item_region != filter_region:
                    continue
            if guid and item_guid != guid.lower():
                continue
            yield complex_dir, summary


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding='utf-8'))


def _attach_images(listing: PropertyListing, files: list[Path], *, replace: bool) -> int:
    if replace:
        for img in listing.images.all():
            img.image.delete(save=False)
            img.delete()
    count = 0
    for idx, path in enumerate(files, start=1):
        if not path.is_file():
            continue
        with path.open('rb') as fh:
            prop_image = PropertyImage(property=listing, sort_order=idx)
            prop_image.image.save(path.name, File(fh), save=True)
            count += 1
    return count


def _attach_unit_image(unit: PropertyListingUnit, path: Path | None) -> None:
    if not path or not path.is_file():
        return
    with path.open('rb') as fh:
        unit.image.save(path.name, File(fh), save=True)


@transaction.atomic
def import_complex(
    complex_dir: Path,
    summary: dict,
    *,
    export_root: Path,
    agent,
    category: PropertyCategory,
    publish: bool,
    replace_units: bool,
    replace_images: bool,
    dry_run: bool = False,
) -> tuple[PropertyListing | None, dict]:
    guid = (summary.get('guid') or complex_dir.name).lower()
    region = resolve_export_region(summary, complex_dir)
    stats = {
        'guid': guid,
        'name': summary.get('name'),
        'units': 0,
        'images': 0,
        'created': False,
        'updated': False,
    }

    apartments_path = complex_dir / 'apartments.json'
    images_index_path = complex_dir / 'images_index.json'
    if not apartments_path.is_file():
        stats['error'] = 'нет apartments.json'
        return None, stats

    apartments = _load_json(apartments_path)
    images_index = _load_json(images_index_path) if images_index_path.is_file() else []
    url_to_file: dict[str, Path] = {}
    for row in images_index:
        rel = (row.get('file') or '').replace('\\', '/')
        url = row.get('url')
        if rel and url:
            url_to_file[url] = export_root / rel

    plan_urls = {a.get('plan_image_url') for a in apartments if a.get('plan_image_url')}
    gallery_files: list[Path] = []
    seen_urls: set[str] = set()
    for row in images_index:
        url = row.get('url')
        rel = (row.get('file') or '').replace('\\', '/')
        if not url or url in plan_urls or url in seen_urls:
            continue
        path = export_root / rel
        if path.is_file():
            gallery_files.append(path)
            seen_urls.add(url)

    district = _resolve_district(region, summary.get('district') or '')
    price_min = _decimal(summary.get('price_min')) or Decimal('0')
    subway_note = _subway_note(summary.get('subways') or [])
    description = clean_listing_description(summary.get('description_html') or '')

    listing = PropertyListing.objects.filter(slug=guid).first()
    created = listing is None
    if dry_run:
        stats['created'] = created
        stats['updated'] = not created
        stats['units'] = len([a for a in apartments if 'брон' not in (a.get('status') or '').lower()])
        stats['images'] = len(gallery_files)
        return listing, stats

    if listing is None:
        listing = PropertyListing(agent=agent, slug=guid)

    listing.agent = agent
    listing.category = category
    listing.name = summary.get('name') or guid
    listing.slug = guid
    listing.region = region
    listing.settlement = SETTLEMENT_BY_REGION.get(region, '')
    listing.district = district
    listing.address = summary.get('address') or ''
    listing.latitude = _decimal(summary.get('latitude'))
    listing.longitude = _decimal(summary.get('longitude'))
    listing.price = price_min
    listing.description = description
    listing.status = (
        PropertyListing.Status.PUBLISHED if publish else PropertyListing.Status.MODERATION
    )
    listing.save()

    details, _ = ResidentialListingDetails.objects.get_or_create(listing=listing)
    details.developer = summary.get('developer') or ''
    details.district_note = summary.get('district') or ''
    details.units_available = summary.get('apartments_count')
    details.units_total = summary.get('apartments_count')
    if price_min and summary.get('apartments_count'):
        sample_area = next(
            (_decimal(a.get('area_total')) for a in apartments if _decimal(a.get('area_total'))),
            None,
        )
        if sample_area and sample_area > 0:
            details.price_per_sqm_from = (price_min / sample_area).quantize(Decimal('0.01'))
    details.travel_time_note = subway_note
    details.save()

    if replace_units:
        for unit in listing.units.all():
            if unit.image:
                unit.image.delete(save=False)
            unit.delete()

    sort_order = 0
    for apt in apartments:
        status = (apt.get('status') or '').lower()
        if status and 'свобод' not in status and 'free' not in status:
            continue
        price = _decimal(apt.get('price'))
        if price is None:
            continue
        rooms, is_studio, layout_label = _parse_rooms(apt)
        sort_order += 1
        unit = PropertyListingUnit(
            listing=listing,
            layout_label=layout_label,
            title=_unit_title(apt),
            building=(apt.get('building') or '')[:64],
            completion_text=_format_deadline(apt.get('deadline')),
            rooms=rooms,
            is_studio=is_studio,
            price=price,
            total_area=_decimal(apt.get('area_total')),
            kitchen_area=_decimal(apt.get('area_kitchen')),
            floor=apt.get('floor'),
            floors_total=apt.get('floors_total'),
            finishing=(apt.get('finishing') or '')[:255],
            sort_order=sort_order,
        )
        unit.save()
        plan_url = apt.get('plan_image_url')
        if plan_url:
            _attach_unit_image(unit, url_to_file.get(plan_url))
        stats['units'] += 1

    stats['images'] = _attach_images(listing, gallery_files, replace=replace_images)
    stats['created'] = created
    stats['updated'] = not created
    return listing, stats


def import_all(
    export_root: Path,
    *,
    region: str | None = None,
    guid: str | None = None,
    agent_username: str | None = None,
    publish: bool = True,
    replace_units: bool = True,
    replace_images: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    agent = _ensure_agent(agent_username)
    category = _ensure_category()
    results: list[dict] = []
    for complex_dir, summary in iter_export_complexes(export_root, region=region, guid=guid):
        _, stats = import_complex(
            complex_dir,
            summary,
            export_root=export_root,
            agent=agent,
            category=category,
            publish=publish,
            replace_units=replace_units,
            replace_images=replace_images,
            dry_run=dry_run,
        )
        results.append(stats)
    return results
