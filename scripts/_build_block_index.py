# -*- coding: utf-8 -*-
import json
import requests
from collections import OrderedDict

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

# build block index from apartments pages
blocks = OrderedDict()
for offset in range(0, 2000, 100):
    r = s.get(base + '/apartments/search', headers=headers, params={'city': city, 'count': 100, 'offset': offset}, timeout=60)
    data = r.json().get('data') or {}
    lst = data.get('list') or []
    for it in lst:
        bid = it.get('block_id')
        if bid and bid not in blocks:
            blocks[bid] = it.get('block_name')
    print('offset', offset, 'unique blocks', len(blocks), 'page', len(lst))
    if len(lst) < 100:
        break

targets = [
    'Аструм', 'ELEMENT', 'Моисеенко', 'Остров Первых', 'Коллекционер',
    'Новый Московский', 'Зум на Неве', 'Гений', 'Галерная Гавань',
    'Новое Колпино', 'Тайм Сквер', 'Респект',
]
print('\nMATCHES:')
for t in targets:
    for bid, name in blocks.items():
        if t.lower() in (name or '').lower():
            print(' ', t, '->', name, bid)

open('data/spb_block_index_partial.json', 'w', encoding='utf-8').write(
    json.dumps(blocks, ensure_ascii=False, indent=2)
)
