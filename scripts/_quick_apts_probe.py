# -*- coding: utf-8 -*-
import json
import os
import requests

phone = os.environ.get('TRENDAGENT_PHONE', '+79650412059')
password = os.environ.get('TRENDAGENT_PASSWORD', 'N7FXpa6')
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
city = '58c665588b6aa52311afa01b'
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

# find astrum in list pages
found = []
offset = 0
while offset <= 2000:
    r = s.get(f'{base}/blocks/search', headers=headers, params={
        'city': city, 'show_type': 'list', 'count': 50, 'offset': offset,
    }, timeout=60)
    results = (r.json().get('data') or {}).get('results') or []
    if not results:
        break
    for item in results:
        if (item.get('guid') or '').lower() == 'astrum':
            found.append({'offset': offset, '_id': item.get('_id'), 'name': item.get('name'), 'guid': item.get('guid')})
    offset += 50

print('astrum list matches:', json.dumps(found, ensure_ascii=False, indent=2))

for block_id in ['5fbbc8b7a4336b0008df6fda', '68b02bf413edc6d8443e8f23']:
    r = s.get(f'{base}/apartments/search', headers=headers, params={
        'city': city, 'block_id': block_id, 'count': 100, 'offset': 0,
    }, timeout=60)
    d = r.json().get('data') or {}
    lst = d.get('list') or []
    print(f'block_id={block_id}: apartmentsCount={d.get("apartmentsCount")} page={len(lst)} first_block={lst[0].get("block_name") if lst else None}')
