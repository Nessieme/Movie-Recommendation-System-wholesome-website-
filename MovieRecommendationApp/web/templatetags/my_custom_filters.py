# MovieRecommendationApp/web/templatetags/my_custom_filters.py

from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Custom filter to allow dictionary lookup by variable key in Django templates.
    Usage: {{ dictionary|get_item:key_variable }}
    """
    return dictionary.get(key)