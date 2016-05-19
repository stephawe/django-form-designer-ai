from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from form_designer.models import FormDefinition


class CMSFormDefinition(CMSPlugin):
    form_definition = models.ForeignKey(FormDefinition, verbose_name=_('form'))

    def __unicode__(self):
        return self.form_definition.__unicode__()
