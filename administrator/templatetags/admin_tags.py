from django import template
from administrator.utils import user_is_admin

register = template.Library()


@register.filter
def is_admin(user):
    """Return True if user is Admin (superuser or in Admin group). Use to show/hide Administrator Control."""
    return user_is_admin(user)
