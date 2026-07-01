"""Поиск и удаление дубликатов PropertyListing (один ЖК — несколько карточек)."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from apps.accounts.models import PropertyListing

NUMERIC_SLUG_SUFFIX = re.compile(r'^(.+)-(\d+)$')


@dataclass
class DuplicateGroup:
    listings: list[PropertyListing]
    canonical: PropertyListing
    to_remove: list[PropertyListing]
    match_reason: str


def slug_base(slug: str) -> str:
    slug = (slug or '').strip()
    if not slug:
        return ''
    match = NUMERIC_SLUG_SUFFIX.match(slug)
    if match:
        return match.group(1)
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


def _slug_cluster_key(slug: str) -> str:
    """Ключ кластера: ostrov-pervyh-3 → ostrov-pervyh; trend-144-9 остаётся trend-144-9."""
    slug = (slug or '').strip()
    if not slug:
        return ''
    if NUMERIC_SLUG_SUFFIX.match(slug):
        return slug_base(slug)
    return slug


def _union_find_groups(listings: list[PropertyListing]) -> list[list[PropertyListing]]:
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
            key = _slug_cluster_key(listing.slug)
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


def _canonical_score(listing: PropertyListing, known_guids: set[str]) -> tuple[int, int, int]:
    slug = (listing.slug or '').strip().lower()
    units_count = listing.units.count()
    score = 0
    if slug in known_guids:
        score += 100_000
    if slug and not NUMERIC_SLUG_SUFFIX.match(slug):
        score += 10_000
    score += units_count * 100
    if listing.status == PropertyListing.Status.PUBLISHED:
        score += 10
    return (score, units_count, -listing.pk)


def pick_canonical(
    listings: list[PropertyListing],
    known_guids: set[str],
) -> PropertyListing:
    return max(listings, key=lambda item: _canonical_score(item, known_guids))


def _match_reason(listings: list[PropertyListing]) -> str:
    names = {(item.name or '').strip().lower() for item in listings}
    bases = {slug_base(item.slug) for item in listings if item.slug}
    if len(names) == 1 and len(bases) == 1:
        return 'одинаковое имя и slug-base'
    if len(names) == 1:
        return 'одинаковое имя'
    if len(bases) == 1:
        return 'одинаковый slug-base'
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
    for raw_group in _union_find_groups(listings):
        canonical = pick_canonical(raw_group, guids)
        to_remove = [item for item in raw_group if item.pk != canonical.pk]
        groups.append(
            DuplicateGroup(
                listings=sorted(raw_group, key=lambda item: item.pk),
                canonical=canonical,
                to_remove=sorted(to_remove, key=lambda item: item.pk),
                match_reason=_match_reason(raw_group),
            )
        )

    groups.sort(key=lambda group: (-len(group.listings), group.canonical.name.lower()))
    return groups


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
