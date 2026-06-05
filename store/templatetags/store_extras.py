from django import template

# This variable MUST be named exactly 'register'
register = template.Library()

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def trim(value):
    return value.strip()