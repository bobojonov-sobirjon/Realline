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

# find block via apartments search by block name in results
targets = ['Аструм', 'ELEMENT', 'Моисеенко', 'Остров Первых', 'Коллекционер']
for t in targets:
    r = s.get(base + '/apartments/search', headers=headers, params={'city': city, 'query': t, 'count': 50}, timeout=30)
    items = (r.json().get('data') or {}).get('list') or []
    blocks = {}
    for it in items:
        bn = it.get('block_name') or ''
        if t.lower() in bn.lower() or t.lower() in (it.get('block_guid') or ''):
            blocks[it['block_id']] = bn
    print(t, 'blocks', blocks)
