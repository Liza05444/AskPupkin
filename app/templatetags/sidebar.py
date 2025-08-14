from django import template
from django.core.cache import cache

register = template.Library()

@register.inclusion_tag('layouts/popular_tags.html')
def popular_tags():
    tags = cache.get('popular_tags', [])
    return {'tags': tags}

@register.inclusion_tag('layouts/top_users.html')
def top_users():
    users = cache.get('top_users', [])
    return {'users': users}
