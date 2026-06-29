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

# blocks search
for params in [
    {'query': 'Аструм', 'city': city_id},
    {'text': 'Аструм', 'city': city_id},
    {'name': 'Аструм', 'city': city_id},
    {'search': 'Аструм', 'city': city_id},
]:
    r = s.get(base + '/blocks/search', headers=headers, params=params, timeout=30)
    print('blocks/search', params, r.status_code)
    if r.ok:
        d = r.json()
        lst = (d.get('data') or {}).get('list') or []
        print(' count', len(lst), [(x.get('name'), x.get('id')) for x in lst[:5]])

# find astrum in blocks list
r = s.get(base + '/blocks/search', headers=headers, params={'query': 'astrum', 'city': city_id}, timeout=30)
if r.ok:
    open('data/blocks_search_astrum.json', 'w', encoding='utf-8').write(json.dumps(r.json(), ensure_ascii=False, indent=2))

# full block detail
block_id = '5fbbc8b7a4336b0008df6fda'  # replace after astrum found
for name in ['Аструм', 'astrum', 'ELEMENT']:
    rs = s.get(base + '/blocks/search', headers=headers, params={'query': name, 'city': city_id}, timeout=30)
    if rs.ok:
        lst = (rs.json().get('data') or {}).get('list') or []
        if lst:
            block_id = lst[0].get('id') or lst[0].get('_id')
            print('FOUND', name, block_id, lst[0].get('name'))
            break

r = s.get(f'{base}/blocks/{block_id}', headers=headers, params={'city': city_id}, timeout=30)
open('data/block_detail.json', 'w', encoding='utf-8').write(json.dumps(r.json(), ensure_ascii=False, indent=2))
print('block detail keys', list((r.json().get('data') or {}).keys())[:40])

# apartments pagination
all_apts = []
offset = 0
while True:
    r = s.get(base + '/apartments/search', headers=headers, params={
        'city': city_id,
        'block_id': block_id,
        'offset': offset,
        'limit': 50,
    }, timeout=30)
    d = r.json()
    lst = (d.get('data') or {}).get('list') or []
    all_apts.extend(lst)
    print('apts page', offset, len(lst), 'total', len(all_apts))
    if len(lst) < 50:
        break
    offset += 50
    if offset > 500:
        break

open('data/block_apartments.json', 'w', encoding='utf-8').write(json.dumps(all_apts, ensure_ascii=False, indent=2))
if all_apts:
    print('apt sample keys', list(all_apts[0].keys()))
