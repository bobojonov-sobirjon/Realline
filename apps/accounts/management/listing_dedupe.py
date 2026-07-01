"""Поиск и удаление дубликатов PropertyListing (один ЖК — несколько карточек)."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from apps.accounts.models import PropertyListing

NUMERIC_SLUG_SUFFIX = re.compile(r'^(.+)-(\d+)$')
HEX_SLUG_SUFFIX = re.compile(r'^(.+)-([a-f0-9]{6,8})$', re.IGNORECASE)


@dataclass
class DuplicateGroup:
    listings: list[PropertyListing]
    canonical: PropertyListing
    to_remove: list[PropertyListing]
    match_reason: str
    cluster_key: str
    reimport_guid: str | None = None


def slug_base(slug: str) -> str:
    slug = (slug or '').strip()
    if not slug:
        return ''
    match = NUMERIC_SLUG_SUFFIX.match(slug)
    if match:
        return match.group(1)
    return slug


def has_generated_slug_suffix(slug: str, known_guids: set[str] | None = None) -> bool:
    slug = (slug or '').strip().lower()
    if not slug:
        return False
    guids = known_guids or set()
    if slug in guids:
        return False
    if HEX_SLUG_SUFFIX.match(slug):
        return True
    match = NUMERIC_SLUG_SUFFIX.match(slug)
    if match and match.group(1).lower() in guids:
        return True
    return False


def slug_cluster_key(slug: str, known_guids: set[str] | None = None) -> str:
    """
    Ключ кластера дубликатов:
    - ostrov-pervyh-26 → ostrov-pervyh
    - 1733-dced35 → 1733
    - zhk-mira-f32b79 → zhk-mira
    - trend-144-9 → trend-144-9 (guid целиком, не схлопываем)
    """
    slug = (slug or '').strip().lower()
    if not slug:
        return ''
    guids = known_guids or set()

    if slug in guids:
        return slug

    match = HEX_SLUG_SUFFIX.match(slug)
    if match:
        return match.group(1).lower()

    match = NUMERIC_SLUG_SUFFIX.match(slug)
    if match:
        base = match.group(1).lower()
        if base in guids:
            return base
        if not guids:
            return base

    return slug


def load_known_guids(export_root: Path | None) -> set[str]:
    guids: set[str] = set()
    if not export_root or not export_root.is_dir():
        return guids

    index_path = export_root / 'index.json'
    if index_path.is_file():
        try:
            rows = json.loads(index_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            rows = []
        for row in rows:
            guid = (row.get('guid') or '').strip().lower()
            if guid:
                guids.add(guid)

    for region_dir in export_root.iterdir():
        if not region_dir.is_dir():
            continue
        for complex_dir in region_dir.iterdir():
            if complex_dir.is_dir():
                guids.add(complex_dir.name.lower())
            summary_path = complex_dir / 'summary.json'
            if summary_path.is_file():
                try:
                    summary = json.loads(summary_path.read_text(encoding='utf-8'))
                except (json.JSONDecodeError, OSError):
                    continue
                guid = (summary.get('guid') or complex_dir.name).strip().lower()
                if guid:
                    guids.add(guid)
    return guids


def _union_find_groups(
    listings: list[PropertyListing],
    known_guids: set[str],
) -> list[list[PropertyListing]]:
    if not listings:
        return []

    parent = {listing.pk: listing.pk for listing in listings}

    def find(pk: int) -> int:
        while parent[pk] != pk:
            parent[pk] = parent[parent[pk]]
            pk = parent[pk]
        return pk

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_name_region: dict[tuple[str, str], list[PropertyListing]] = defaultdict(list)
    for listing in listings:
        name = (listing.name or '').strip().lower()
        if name:
            by_name_region[(name, listing.region)].append(listing)

    for bucket in by_name_region.values():
        if len(bucket) < 2:
            continue
        by_slug_cluster: dict[str, list[PropertyListing]] = defaultdict(list)
        for listing in bucket:
            key = slug_cluster_key(listing.slug, known_guids)
            if key:
                by_slug_cluster[key].append(listing)
        for cluster in by_slug_cluster.values():
            if len(cluster) < 2:
                continue
            head = cluster[0].pk
            for other in cluster[1:]:
                union(head, other.pk)

    grouped: dict[int, list[PropertyListing]] = defaultdict(list)
    for listing in listings:
        grouped[find(listing.pk)].append(listing)

    return [group for group in grouped.values() if len(group) > 1]


def _canonical_score(
    listing: PropertyListing,
    known_guids: set[str],
    cluster_key: str,
) -> tuple[int, int, int, int]:
    slug = (listing.slug or '').strip().lower()
    units_count = listing.units.count()
    score = 0
    if slug in known_guids:
        score += 100_000
    if cluster_key and slug == cluster_key:
        score += 50_000
    if slug and not has_generated_slug_suffix(slug, known_guids):
        score += 10_000
    score += units_count * 100
    if listing.status == PropertyListing.Status.PUBLISHED:
        score += 10
    return (score, units_count, -len(slug), -listing.pk)


def pick_canonical(
    listings: list[PropertyListing],
    known_guids: set[str],
    cluster_key: str,
) -> PropertyListing:
    return max(
        listings,
        key=lambda item: _canonical_score(item, known_guids, cluster_key),
    )


def resolve_cluster_key(listings: list[PropertyListing], known_guids: set[str]) -> str:
    keys = {slug_cluster_key(item.slug, known_guids) for item in listings if item.slug}
    keys.discard('')
    if not keys:
        return ''
    for item in listings:
        slug = (item.slug or '').strip().lower()
        if slug in known_guids:
            return slug
    for key in keys:
        if key in known_guids:
            return key
    return sorted(keys, key=len)[0]


def resolve_reimport_guid(listings: list[PropertyListing], known_guids: set[str]) -> str | None:
    for item in listings:
        slug = (item.slug or '').strip().lower()
        if slug in known_guids:
            return slug
    cluster_key = resolve_cluster_key(listings, known_guids)
    if cluster_key in known_guids:
        return cluster_key
    return None


def resolve_target_slug(
    canonical: PropertyListing,
    listings: list[PropertyListing],
    known_guids: set[str],
    cluster_key: str,
) -> str:
    for item in listings:
        slug = (item.slug or '').strip().lower()
        if slug in known_guids:
            return slug

    if cluster_key in known_guids:
        return cluster_key

    clean_candidates = sorted(
        {
            (item.slug or '').strip().lower()
            for item in listings
            if item.slug and not has_generated_slug_suffix(item.slug, known_guids)
        },
        key=len,
    )
    if clean_candidates:
        return clean_candidates[0]

    if cluster_key:
        return cluster_key
    return (canonical.slug or '').strip().lower()


def _match_reason(listings: list[PropertyListing], cluster_key: str) -> str:
    names = {(item.name or '').strip().lower() for item in listings}
    if len(names) == 1:
        if cluster_key:
            return f'одинаковое имя, slug-кластер «{cluster_key}»'
        return 'одинаковое имя'
    if cluster_key:
        return f'slug-кластер «{cluster_key}»'
    return 'связанные дубликаты'


def find_duplicate_groups(
    queryset=None,
    *,
    known_guids: set[str] | None = None,
) -> list[DuplicateGroup]:
    qs = queryset if queryset is not None else PropertyListing.objects.all()
    listings = list(qs.order_by('id'))
    guids = known_guids or set()

    groups: list[DuplicateGroup] = []
    for raw_group in _union_find_groups(listings, guids):
        cluster_key = resolve_cluster_key(raw_group, guids)
        canonical = pick_canonical(raw_group, guids, cluster_key)
        to_remove = [item for item in raw_group if item.pk != canonical.pk]
        groups.append(
            DuplicateGroup(
                listings=sorted(raw_group, key=lambda item: item.pk),
                canonical=canonical,
                to_remove=sorted(to_remove, key=lambda item: item.pk),
                match_reason=_match_reason(raw_group, cluster_key),
                cluster_key=cluster_key,
                reimport_guid=resolve_reimport_guid(raw_group, guids),
            )
        )

    groups.sort(key=lambda group: (-len(group.listings), group.canonical.name.lower()))
    return groups


def normalize_canonical_slugs(
    groups: list[DuplicateGroup],
    known_guids: set[str],
    *,
    execute: bool,
) -> int:
    renamed = 0
    for group in groups:
        canonical = group.canonical
        target_slug = resolve_target_slug(canonical, group.listings, known_guids, group.cluster_key)
        if not target_slug or canonical.slug.lower() == target_slug:
            continue
        conflict = (
            PropertyListing.objects.filter(slug=target_slug)
            .exclude(pk=canonical.pk)
            .exists()
        )
        if conflict:
            continue
        if execute:
            canonical.slug = target_slug
            canonical.save(update_fields=['slug'])
        renamed += 1
    return renamed


def apply_cleanup(
    groups: list[DuplicateGroup],
    *,
    execute: bool,
) -> dict:
    stats = {
        'groups': len(groups),
        'removed': 0,
        'kept': 0,
        'removed_units': 0,
        'renamed': 0,
    }
    for group in groups:
        stats['kept'] += 1
        for listing in group.to_remove:
            units_count = listing.units.count()
            stats['removed_units'] += units_count
            if execute:
                listing.delete()
            stats['removed'] += 1
    return stats
