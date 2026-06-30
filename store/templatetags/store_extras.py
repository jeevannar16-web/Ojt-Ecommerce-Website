# Module: store.templatetags.store_extras
# Description: Extra template tags for store app

from django import template
import re

register = template.Library()


CLOUDINARY_RE = re.compile(r'^(https?://res\.cloudinary\.com/[^/]+/image/upload/)(.+)$')

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def trim(value):
    return value.strip()

@register.filter
def dict_key(value, key):
    return value.get(key)

@register.filter
def img_url(image, size="300x300"):
    if not image:
        return ''
    if hasattr(image, 'url'):
        url = image.url
    elif hasattr(image, 'name'):
        url = image.name
    else:
        url = str(image)
    url = str(url)
    m = CLOUDINARY_RE.match(url)
    if m:
        base, rest = m.groups()
        return f"{base}c_fill,w_{size.split('x')[0]},h_{size.split('x')[1] if 'x' in size else size.split('x')[0]}/{rest}"
    return url