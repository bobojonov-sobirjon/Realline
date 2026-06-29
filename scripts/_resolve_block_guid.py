# -*- coding: utf-8 -*-
import json
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})

login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': '+79650412059', 'password': 'N7FXpa6'}, timeout=30).json()
token = login['auth_token']
city = login['user']['agency']['city']['_id']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'
guid = 'astrum'

for params in [
    {'city': city, 'show_type': 'list', 'count': 5, 'offset': 0, 'guid': guid},
    {'city': city, 'show_type': 'list', 'count': 5, 'offset': 0, 'block_guid': guid},
    {'city': city, 'show_type': 'list', 'count': 5, 'offset': 0, 'block': guid},
    {'city': city, 'show_type': 'list', 'count': 5, 'offset': 0, 'text': 'Аструм'},
]:
    r = s.get(base + '/blocks/search', headers=headers, params=params, timeout=60)
    res = (r.json().get('data') or {}).get('results') or []
    print(params, '->', [(x.get('name'), x.get('id'), x.get('guid')) for x in res[:3]])

for path in [f'/blocks/guid/{guid}', f'/block/{guid}', f'/blocks/by-guid/{guid}']:
    r = s.get(base + path, headers=headers, params={'city': city}, timeout=30)
    print(path, r.status_code, r.text[:200])

# apartments search - get block_id from first apt
r = s.get(base + '/apartments/search', headers=headers, params={'city': city, 'query': 'Аструм', 'count': 50}, timeout=60)
for it in (r.json().get('data') or {}).get('list') or []:
    if (it.get('block_guid') or '') == guid or 'аструм' in (it.get('block_name') or '').lower():
        print('apt block', it.get('block_id'), it.get('block_name'), it.get('block_guid'))
        bid = it.get('block_id')
        break
else:
    bid = None

if bid:
    r = s.get(f'{base}/blocks/{bid}', headers=headers, params={'city': city}, timeout=30)
    print('detail', r.json().get('data', {}).get('name'))
