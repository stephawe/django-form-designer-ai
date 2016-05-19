from django.db import models
from django.utils.encoding import force_text
from django.utils.six import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from form_designer.models import FormDefinition


@python_2_unicode_compatible
class CMSFormDefinition(CMSPlugin):
    form_definition = models.ForeignKey(FormDefinition, verbose_name=_('form'))

    def __str__(self):
        return force_text(self.form_definition)
