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
    'Origin': 'https://spb.trendagent.ru',
    'Referer': 'https://spb.trendagent.ru/',
})
login = s.post('https://sso-api.trendagent.ru/v1/login', json={'phone': phone, 'password': password}, timeout=60).json()
token = login['auth_token']
city = '58c665588b6aa52311afa01b'
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

for block_id in ['5fbbc8b7a4336b0008df6fda', '68b02bf413edc6d8443e8f23']:
    r = s.get(f'{base}/blocks/{block_id}', headers=headers, params={'city': city}, timeout=60)
    d = r.json().get('data') or {}
    print(block_id, '->', d.get('name'), d.get('guid'), 'apts?', d.get('apartmentsCount') or d.get('apartments_count'))
