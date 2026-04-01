from apps.accounts.models import PropertyTag


def sync_property_tags(listing, items):
    """
    Полная синхронизация тегов объекта с переданным списком.
    items: [{"tag_name": "..."}, ...] или [{"id": 1, "tag_name": "..."}, ...]
    Элементы без id (или с несуществующим id) создаются; существующие id обновляются;
    отсутствующие в списке теги удаляются.
    """
    if items is None:
        return
    keep_ids = []
    for item in items:
        tag_name = item['tag_name'].strip()
        if not tag_name:
            continue
        tid = item.get('id')
        if tid is not None:
            t = PropertyTag.objects.filter(pk=tid, listing_id=listing.pk).first()
            if t:
                t.tag_name = tag_name
                t.save(update_fields=['tag_name'])
                keep_ids.append(t.pk)
                continue
        t = PropertyTag.objects.create(listing=listing, tag_name=tag_name)
        keep_ids.append(t.pk)
    PropertyTag.objects.filter(listing=listing).exclude(pk__in=keep_ids).delete()
