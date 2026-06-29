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

# all blocks via map
r = s.get(base + '/blocks/search', headers=headers, params={'city': city, 'show_type': 'map'}, timeout=120)
results = (r.json().get('data') or {}).get('results') or []
print('all blocks', len(results))
open('data/spb_all_blocks_map.json', 'w', encoding='utf-8').write(
    json.dumps([{'id': b.get('id'), 'name': b.get('name'), 'guid': b.get('guid')} for b in results], ensure_ascii=False, indent=2)
)

targets = [
    'Аструм', 'ELEMENT', 'Моисеенко', 'Остров Первых', 'Коллекционер',
    'Новый Московский', 'Зум на Неве', 'Гений', 'Галерная Гавань',
    'Новое Колпино', 'Тайм Сквер', 'Респект',
]
for t in targets:
    for b in results:
        name = b.get('name') or ''
        if t.lower() in name.lower():
            print('FOUND', t, '->', name, b.get('id'), b.get('guid'))

# text search
for t in ['Аструм', 'ELEMENT']:
    for key in ['text', 'query', 'name']:
        r2 = s.get(base + '/blocks/search', headers=headers, params={
            'city': city, 'show_type': 'list', 'count': 20, 'offset': 0, key: t,
        }, timeout=60)
        res = (r2.json().get('data') or {}).get('results') or []
        print('search', key, t, '->', [(x.get('name'), x.get('id')) for x in res[:5]])
