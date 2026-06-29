import re
cfg = open('data/spb_config.js', encoding='utf-8').read()
for pat in ['blocks/search', 'apartments/search', 'show_type', 'block_id']:
    idx = 0
    while True:
        i = cfg.find(pat, idx)
        if i == -1:
            break
        print('---', pat, '---')
        print(cfg[max(0, i - 120): i + 200])
        idx = i + len(pat)
        if idx > 500000:
            break
