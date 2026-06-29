# -*- coding: utf-8 -*-
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://msk.trendagent.ru',
    'Referer': 'https://msk.trendagent.ru/',
})

login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': '+79650412059', 'password': 'N7FXpa6'}, timeout=30).json()
token = login['auth_token']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

for city_id, label in [
    ('58c665588b6aa52311afa01a', 'msk_a'),
    ('58c665588b6aa52311afa019', 'msk_19'),
    ('58c665588b6aa52311afa01c', 'msk_c'),
]:
    r = s.get(base + '/blocks/search', headers=headers, params={'city': city_id, 'show_type': 'map'}, timeout=120)
    if r.ok:
        res = (r.json().get('data') or {}).get('results') or []
        print(label, city_id, 'blocks', len(res), 'sample', res[0].get('name') if res else None)
