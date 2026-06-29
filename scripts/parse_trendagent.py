#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер ЖК и квартир с trendagent.ru (официальный API агентского кабинета).

Использование:
  set TRENDAGENT_PHONE=+79650412059
  set TRENDAGENT_PASSWORD=your_password
  python scripts/parse_trendagent.py
  python scripts/parse_trendagent.py --city spb
  python scripts/parse_trendagent.py --guid astrum
  python scripts/parse_trendagent.py --output data/trendagent_export

Результат:
  data/trendagent_export/<region>/<slug>/
    block.json          — карточка ЖК
    apartments.json     — все квартиры в продаже
    images/             — фото ЖК и планировки
    summary.json        — краткая сводка для импорта на сайт
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

# --- constants ---
SSO_LOGIN_URL = 'https://sso-api.trendagent.ru/v1/login'
API_BASE = 'https://api.trendagent.ru/v4_29'
IMG_CDN = 'https://selcdn.trendagent.ru/images/'
SCRIPT_DIR = Path(__file__).resolve().parent
TARGETS_FILE = SCRIPT_DIR / 'trendagent_targets.json'
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / 'data' / 'trendagent_export'
PAGE_SIZE = 100


class TrendAgentClient:
    def __init__(self, phone: str, password: str, origin: str = 'https://spb.trendagent.ru'):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': origin,
            'Referer': f'{origin}/',
        })
        self.phone = phone
        self.password = password
        self.token: str | None = None
        self.user_city_id: str | None = None

    def login(self) -> dict[str, Any]:
        r = self.session.post(
            SSO_LOGIN_URL,
            json={'phone': self.phone, 'password': self.password},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        self.token = data['auth_token']
        self.user_city_id = data['user']['agency']['city']['_id']
        self.session.headers['Authorization'] = f'Bearer {self.token}'
        return data

    def _get(self, path: str, *, city_id: str, params: dict | None = None, timeout: int = 120) -> dict:
        p = {'city': city_id, **(params or {})}
        url = f'{API_BASE}{path}'
        r = self.session.get(url, params=p, timeout=timeout)
        if r.status_code == 401:
            self.login()
            r = self.session.get(url, params=p, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def fetch_blocks_map(self, city_id: str) -> list[dict]:
        data = self._get('/blocks/search', city_id=city_id, params={'show_type': 'map'}, timeout=180)
        return (data.get('data') or {}).get('results') or []

    def fetch_blocks_list_index(self, city_id: str) -> dict[str, dict]:
        """guid -> list item с Mongo _id (один проход по list API)."""
        index: dict[str, dict] = {}
        offset = 0
        while True:
            data = self._get(
                '/blocks/search',
                city_id=city_id,
                params={'show_type': 'list', 'count': 50, 'offset': offset},
                timeout=120,
            )
            results = (data.get('data') or {}).get('results') or []
            if not results:
                break
            for item in results:
                guid = (item.get('guid') or '').strip().lower()
                if guid:
                    index[guid] = item
            offset += len(results)
        return index

    def resolve_block_list_item(
        self,
        city_id: str,
        *,
        guid: str | None = None,
        name: str | None = None,
        list_index: dict[str, dict] | None = None,
    ) -> dict | None:
        """Находит ЖК в list-выдаче (там есть _id для detail API)."""
        needle_guid = (guid or '').strip().lower()
        if needle_guid and list_index and needle_guid in list_index:
            return list_index[needle_guid]

        needle_name = (name or '').strip().lower()
        if list_index and needle_name:
            for item in list_index.values():
                item_name = (item.get('name') or '').lower()
                if needle_name in item_name or item_name in needle_name:
                    return item

        offset = 0
        while True:
            data = self._get(
                '/blocks/search',
                city_id=city_id,
                params={'show_type': 'list', 'count': 50, 'offset': offset},
                timeout=120,
            )
            results = (data.get('data') or {}).get('results') or []
            if not results:
                return None
            for item in results:
                item_guid = (item.get('guid') or '').lower()
                item_name = (item.get('name') or '').lower()
                if needle_guid and item_guid == needle_guid:
                    return item
                if needle_name and (needle_name in item_name or item_name in needle_name):
                    return item
            offset += len(results)
            if offset > 10000:
                return None

    def fetch_block_detail(self, city_id: str, block_id: str) -> dict:
        data = self._get(f'/blocks/{block_id}', city_id=city_id, timeout=120)
        return data.get('data') or {}

    def fetch_apartments(self, city_id: str, block_id: str) -> list[dict]:
        """Квартиры одного ЖК. API фильтрует по параметру block (не block_id!)."""
        all_items: list[dict] = []
        offset = 0
        total_expected: int | None = None
        while True:
            data = self._get(
                '/apartments/search',
                city_id=city_id,
                params={'block': block_id, 'count': PAGE_SIZE, 'offset': offset},
                timeout=120,
            )
            payload = data.get('data') or {}
            if total_expected is None:
                total_expected = payload.get('apartmentsCount')
            chunk = payload.get('list') or []
            all_items.extend(chunk)
            if total_expected is not None and len(all_items) >= total_expected:
                break
            if len(chunk) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return all_items


def load_targets() -> dict:
    with TARGETS_FILE.open(encoding='utf-8') as f:
        return json.load(f)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r'[^\w\s-]', '', value, flags=re.UNICODE)
    value = re.sub(r'[\s_]+', '-', value)
    return value[:80] or 'complex'


def plan_image_url(plan: dict | None) -> str | None:
    if not plan:
        return None
    path = (plan.get('path') or '').strip()
    fname = (plan.get('file_name') or '').strip()
    if path and fname:
        return f'{IMG_CDN}{path}{fname}'
    return None


def block_image_url(image: dict | None) -> str | None:
    if not image:
        return None
    if image.get('src'):
        return image['src']
    return plan_image_url(image)


def collect_image_urls(block: dict, apartments: list[dict]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    for item in block.get('gallery') or []:
        add(block_image_url(item))
    add(block_image_url(block.get('image')))

    for apt in apartments:
        add(plan_image_url(apt.get('plan')))

    return urls


def download_file(session: requests.Session, url: str, dest: Path) -> bool:
    try:
        r = session.get(url, timeout=120)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return True
    except requests.RequestException as exc:
        print(f'  ! не скачано {url}: {exc}')
        return False


def normalize_apartment(apt: dict) -> dict:
    room = apt.get('room') or {}
    return {
        'id': apt.get('_id'),
        'number': apt.get('number'),
        'block_name': apt.get('block_name'),
        'building': apt.get('building_name'),
        'rooms': room.get('name') or room.get('name_one'),
        'rooms_code': room.get('crm_id'),
        'is_studio': room.get('crm_id') == 0 or 'студ' in (room.get('name') or '').lower(),
        'area_total': apt.get('area_given'),
        'area_kitchen': apt.get('area_kitchen'),
        'floor': apt.get('floor'),
        'floors_total': apt.get('floors'),
        'price': apt.get('price'),
        'price_per_sqm': apt.get('price_m2') or apt.get('price_per_meter'),
        'finishing': (apt.get('finishing') or {}).get('name'),
        'deadline': apt.get('deadline'),
        'status': (apt.get('status') or {}).get('name'),
        'plan_image_url': plan_image_url(apt.get('plan')),
    }


def build_summary(block: dict, apartments: list[dict], *, region: str, source_guid: str) -> dict:
    prices = [a['price'] for a in apartments if a.get('price')]
    return {
        'source': 'trendagent.ru',
        'region': region,
        'guid': source_guid,
        'name': block.get('name'),
        'address': block.get('address'),
        'latitude': block.get('latitude'),
        'longitude': block.get('longitude'),
        'developer': (block.get('builder') or {}).get('name'),
        'district': (block.get('region') or {}).get('name'),
        'description_html': block.get('description'),
        'apartments_count': len(apartments),
        'price_min': min(prices) if prices else block.get('minPrice'),
        'price_max': max(prices) if prices else block.get('maxPrice'),
        'subways': [
            {
                'name': s.get('name'),
                'minutes': s.get('distance_timing'),
                'type': s.get('distance_type'),
            }
            for s in (block.get('subways') or [])
        ],
    }


def names_match(needle: str, haystack: str) -> bool:
    n = needle.strip().lower()
    h = haystack.strip().lower()
    if not n or not h:
        return False
    if n == h:
        return True
    if n in h or h in n:
        return bool(re.search(rf'\b{re.escape(n)}\b', h) or re.search(rf'\b{re.escape(h)}\b', n))
    return False


def match_targets(blocks_map: list[dict], names: list[str], guids: list[str]) -> list[dict]:
    matched: list[dict] = []
    used_guids: set[str] = set()
    used_names: set[str] = set()

    for g in guids:
        g_lower = g.lower()
        for b in blocks_map:
            if (b.get('guid') or '').lower() == g_lower:
                matched.append(b)
                used_guids.add(g_lower)
                used_names.add((b.get('name') or '').lower())
                break

    for name in names:
        n_lower = name.lower()
        if n_lower in used_names:
            continue
        for b in blocks_map:
            g = (b.get('guid') or '').lower()
            if g in used_guids:
                continue
            bname = (b.get('name') or '').lower()
            if names_match(n_lower, bname):
                matched.append(b)
                used_guids.add(g)
                used_names.add(bname)
                break

    return matched


def parse_complex(
    client: TrendAgentClient,
    *,
    city_id: str,
    region: str,
    map_item: dict,
    output_root: Path,
    list_index: dict[str, dict] | None = None,
    folder: str | None = None,
) -> dict | None:
    guid = map_item.get('guid') or slugify(map_item.get('name') or 'complex')
    name = map_item.get('name') or guid
    print(f'\n=== {name} ({guid}) ===')

    list_item = client.resolve_block_list_item(
        city_id, guid=guid, name=name, list_index=list_index,
    )
    if not list_item:
        print('  ! не найден _id в list API')
        return None

    block_id = list_item.get('_id')
    if not block_id:
        print('  ! пустой block_id')
        return None

    block = client.fetch_block_detail(city_id, block_id)
    apartments_raw = client.fetch_apartments(city_id, block_id)
    apartments = [normalize_apartment(a) for a in apartments_raw]
    print(f'  квартир: {len(apartments)}')

    out_dir = output_root / region / slugify(guid)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_urls = collect_image_urls(block, apartments_raw)
    images_dir = out_dir / 'images'
    downloaded: list[dict] = []
    for idx, url in enumerate(image_urls, start=1):
        ext = Path(urlparse(url).path).suffix or '.jpg'
        fname = f'{idx:03d}{ext}'
        dest = images_dir / fname
        if download_file(client.session, url, dest):
            downloaded.append({'file': str(dest.relative_to(output_root)), 'url': url})

    summary = build_summary(block, apartments, region=region, source_guid=guid)
    summary['images_downloaded'] = len(downloaded)
    if folder:
        summary['folder'] = folder

    (out_dir / 'block.json').write_text(json.dumps(block, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'apartments.json').write_text(json.dumps(apartments, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'images_index.json').write_text(json.dumps(downloaded, ensure_ascii=False, indent=2), encoding='utf-8')

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Парсинг ЖК с trendagent.ru')
    parser.add_argument('--phone', default=os.environ.get('TRENDAGENT_PHONE', ''))
    parser.add_argument('--password', default=os.environ.get('TRENDAGENT_PASSWORD', ''))
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--city', choices=['spb', 'msk', 'all'], default='all')
    parser.add_argument('--guid', help='Только один ЖК по guid (например astrum)')
    parser.add_argument('--delay', type=float, default=0.3, help='Пауза между ЖК (сек)')
    args = parser.parse_args(argv)

    if not args.phone or not args.password:
        print('Укажите TRENDAGENT_PHONE и TRENDAGENT_PASSWORD в env или аргументах.', file=sys.stderr)
        return 1

    config = load_targets()
    cities = config['cities']

    # логин (origin по умолчанию СПб)
    client = TrendAgentClient(args.phone, args.password, origin=cities['spb']['origin'])
    user = client.login()
    print(f"Авторизация OK: {user['user'].get('name')} / агентство {user['user']['agency'].get('name')}")

    args.output.mkdir(parents=True, exist_ok=True)
    all_summaries: list[dict] = []

    groups = config['complexes']
    if args.city != 'all':
        groups = [g for g in groups if g['city'] == args.city]

    for group in groups:
        city_key = group['city']
        city_cfg = cities[city_key]
        city_id = city_cfg['city_id']
        region = group.get('region') or city_cfg['region']
        origin = city_cfg['origin']

        if client.session.headers.get('Origin') != origin:
            client.session.headers.update({'Origin': origin, 'Referer': f'{origin}/'})

        print(f"\n--- Город: {city_key} ({city_id}) ---")
        try:
            blocks_map = client.fetch_blocks_map(city_id)
        except requests.HTTPError as exc:
            print(f'  ! нет доступа к городу {city_key}: {exc}')
            continue

        print(f'  ЖК в каталоге: {len(blocks_map)}')
        print('  индекс list API...')
        list_index = client.fetch_blocks_list_index(city_id)
        print(f'  индекс: {len(list_index)} guid')

        if args.guid:
            targets = [b for b in blocks_map if (b.get('guid') or '').lower() == args.guid.lower()]
        else:
            targets = match_targets(
                blocks_map,
                group.get('names') or [],
                group.get('guids') or [],
            )

        print(f'  к парсингу: {len(targets)}')
        for item in targets:
            summary = parse_complex(
                client,
                city_id=city_id,
                region=region,
                map_item=item,
                output_root=args.output,
                list_index=list_index,
                folder=group.get('folder'),
            )
            if summary:
                summary['folder'] = group.get('folder')
                all_summaries.append(summary)
            time.sleep(args.delay)

    index_path = args.output / 'index.json'
    if index_path.exists():
        try:
            existing = json.loads(index_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            existing = []
        by_guid = {(item.get('guid') or '').lower(): item for item in existing if item.get('guid')}
        for item in all_summaries:
            by_guid[(item.get('guid') or '').lower()] = item
        all_summaries = list(by_guid.values())

    index_path.write_text(json.dumps(all_summaries, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nГотово: {len(all_summaries)} ЖК -> {args.output}')
    print(f'Сводка: {index_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
