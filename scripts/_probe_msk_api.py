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
    'Origin': 'https://msk.trendagent.ru',
    'Referer': 'https://msk.trendagent.ru/',
})
login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
token = login['auth_token']
agency_city = login['user']['agency']['city']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'
msk_id = '58c665588b6aa52311afa01a'

print('agency city:', agency_city)

for city_id, label in [(msk_id, 'msk'), (login['user']['agency']['city']['_id'], 'agency')]:
    r = s.get(f'{base}/blocks/search', headers=headers, params={'city': city_id, 'show_type': 'map'}, timeout=120)
    print(label, 'map', r.status_code, end=' ')
    if r.ok:
        blocks = (r.json().get('data') or {}).get('results') or []
        print('blocks', len(blocks))
        open(f'data/msk_blocks_map_{label}.json', 'w', encoding='utf-8').write(
            json.dumps(blocks, ensure_ascii=False, indent=2)
        )
    else:
        print(r.text[:200])
