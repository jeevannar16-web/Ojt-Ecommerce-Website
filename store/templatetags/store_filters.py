# ==============================================================================
# Module: store.templatetags.store_filters
# Description: Template filters for store app
# ==============================================================================

import json
from django import template

register = template.Library()


@register.filter
def pretty_json(value):
    if value is None:
        return ''
    try:
        return json.dumps(value, indent=2)
    except (TypeError, ValueError):
        return str(value)
