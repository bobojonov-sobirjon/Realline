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
city_id = login['user']['agency']['city']['_id']
headers = {**s.headers, 'Authorization': f'Bearer {token}'}
base = 'https://api.trendagent.ru/v4_29'

for path in ['/blocks/search', '/blocks', '/block/search', '/search/blocks', '/complexes/search']:
    for params in [{'query': 'Аструм', 'city': city_id}, {'name': 'Аструм', 'city': city_id}, {'text': 'Аструм', 'city': city_id}, {'city': city_id, 'limit': 2}]:
        r = s.get(base + path, headers=headers, params=params, timeout=20)
        if r.status_code == 200 and r.text[0] == '{':
            d = r.json()
            lst = (d.get('data') or {})
            if isinstance(lst, dict):
                lst = lst.get('list') or lst.get('blocks') or []
            print('OK', path, params, 'items', len(lst) if isinstance(lst, list) else d.keys())
            if isinstance(lst, list) and lst:
                print(' sample', lst[0].get('name') or lst[0].get('block_name'), lst[0].get('_id'))

# block detail by guid
for block_guid in ['astrum', 'meltzer-hall']:
    for path in [f'/blocks/{block_guid}', f'/block/{block_guid}', f'/blocks/guid/{block_guid}']:
        r = s.get(base + path, headers=headers, params={'city': city_id}, timeout=20)
        if r.status_code == 200:
            print('GUID', path, r.text[:300])

# apartments for astrum block search
r = s.get(base + '/apartments/search', headers=headers, params={'query': 'Аструм', 'city': city_id, 'block_name': 'Аструм'}, timeout=30)
items = (r.json().get('data') or {}).get('list') or []
block_ids = {}
for it in items:
    bid = it.get('block_id')
    block_ids[bid] = it.get('block_name')
print('block_ids from apt search', block_ids)

if block_ids:
    bid = list(block_ids.keys())[0]
    for path in [f'/blocks/{bid}', f'/blocks/{bid}/apartments', f'/apartments/search']:
        params = {'city': city_id}
        if 'search' in path:
            params['block_id'] = bid
        r = s.get(base + path, headers=headers, params=params, timeout=30)
        print(path, r.status_code, r.text[:200] if r.status_code==200 else r.text[:100])
        if r.status_code == 200 and path.endswith('search'):
            open('data/apts_by_block.json', 'w', encoding='utf-8').write(json.dumps(r.json(), ensure_ascii=False, indent=2)[:300000])
