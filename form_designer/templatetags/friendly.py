from django import template
from django.db.models.query import QuerySet
from django.template.defaultfilters import yesno
from django.utils.translation import ugettext_lazy as _

register = template.Library()

# Returns a more "human-friendly" representation of value than repr()


def friendly(value, null_value=None):
    if value is None and not (null_value is None):
        return null_value
    if isinstance(value, QuerySet):
        qs = value
        value = []
        for object in qs:
            value.append(object.__unicode__())
    if isinstance(value, list):
        value = ", ".join(value)
    if isinstance(value, bool):
        value = yesno(value, u"%s,%s" % (_('yes'), _('no')),)
    if hasattr(value, 'url'):
        value = value.url
    if not isinstance(value, basestring):
        value = unicode(value)
    return value

register.filter(friendly)
