# -*- coding: utf-8 -*-
"""Подбор guid для имён из trendagent_targets.json по map API."""
import json
import os
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
TARGETS = SCRIPT_DIR / 'trendagent_targets.json'

phone = os.environ.get('TRENDAGENT_PHONE', '')
password = os.environ.get('TRENDAGENT_PASSWORD', '')
if not phone or not password:
    print('Set TRENDAGENT_PHONE and TRENDAGENT_PASSWORD', file=sys.stderr)
    raise SystemExit(1)

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})
login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
token = login['auth_token']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

config = json.loads(TARGETS.read_text(encoding='utf-8'))
group = next(g for g in config['complexes'] if g['folder'] == 'Это по спб')
city_id = config['cities']['spb']['city_id']

r = s.get(f'{base}/blocks/search', headers=headers, params={'city': city_id, 'show_type': 'map'}, timeout=180)
blocks = (r.json().get('data') or {}).get('results') or []
known = {g.lower() for g in group.get('guids') or []}

print('names without guid match:')
for name in group.get('names') or []:
    n = name.lower()
    hit = None
    for b in blocks:
        g = (b.get('guid') or '').lower()
        bn = (b.get('name') or '').lower()
        if g in known:
            continue
        if n in bn or bn in n or any(part in bn for part in n.split() if len(part) > 3):
            hit = b
            break
    if hit:
        print(f'  {name!r} -> guid={hit.get("guid")!r} name={hit.get("name")!r}')
    else:
        print(f'  {name!r} -> NOT FOUND')

print('\nknown guids:')
for g in group.get('guids') or []:
    for b in blocks:
        if (b.get('guid') or '').lower() == g.lower():
            print(f'  {g} -> {b.get("name")}')
            break
    else:
        print(f'  {g} -> missing in map')
