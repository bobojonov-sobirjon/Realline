import json

from rest_framework import serializers


def _split_separate_tag_names(s):
    s = str(s).strip()
    if not s:
        return []
    return [p.strip() for p in s.split(',') if p.strip()]


def normalize_tags_input_to_sync(raw):
    """
    Приводит tags к списку dict для sync_property_tags:
    - ["а","б"], "а,б" -> отдельные теги;
    - [{"id":1,"tag_name":"x"}] -> с сохранением id для обновления.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        if s.startswith('['):
            raw = json.loads(s)
        else:
            return [{'tag_name': n} for n in _split_separate_tag_names(s)]
    if not isinstance(raw, list):
        raise serializers.ValidationError('tags: ожидается массив (JSON) или строка имён.')
    result = []
    for i, x in enumerate(raw):
        if isinstance(x, dict):
            name = (x.get('tag_name') or '').strip()
            if not name:
                continue
            entry = {'tag_name': name}
            if x.get('id') not in (None, ''):
                try:
                    entry['id'] = int(x['id'])
                except (TypeError, ValueError):
                    pass
            result.append(entry)
        elif isinstance(x, str):
            for n in _split_separate_tag_names(x):
                result.append({'tag_name': n})
        else:
            raise serializers.ValidationError(f'tags[{i}]: строка или {{"id","tag_name"}}')
    return result


def coalesce_multipart_tags(post_list):
    """POST.getlist('tags'): несколько полей или одна JSON-строка / "a,b,c"."""
    if not post_list:
        return None
    if len(post_list) == 1:
        one = post_list[0].strip()
        if one.startswith('['):
            try:
                return json.loads(one)
            except json.JSONDecodeError:
                pass
    out = []
    for item in post_list:
        s = str(item).strip()
        if s.startswith('['):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        out.extend(_split_separate_tag_names(s))
    return out
