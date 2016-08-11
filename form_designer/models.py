from __future__ import unicode_literals

import re
from collections import OrderedDict
from decimal import Decimal

import django
from django.conf import settings as django_settings
from django.db import models
from django.utils.deprecation import warn_about_renamed_method
from django.utils.module_loading import import_string
from django.utils.six import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from picklefield.fields import PickledObjectField

from form_designer import settings
from form_designer.fields import ModelNameField, RegexpExpressionField, TemplateCharField, TemplateTextField
from form_designer.utils import get_random_hash, string_template_replace

MAIL_TEMPLATE_CONTEXT_HELP_TEXT = _(
    'Your form fields are available as template context. '
    'Example: "{{ first_name }} {{ last_name }} <{{ from_email }}>" '
    'if you have fields named `first_name`, `last_name`, `from_email`.'
)

class FormValueDict(dict):
    def __init__(self, name, value, label):
        self['name'] = name
        self['value'] = value
        self['label'] = label
        super(FormValueDict, self).__init__()


@python_2_unicode_compatible
class FormDefinition(models.Model):
    name = models.SlugField(_('name'), max_length=255, unique=True)
    require_hash = models.BooleanField(_('obfuscate URL to this form'), default=False, help_text=_('If enabled, the form can only be reached via a secret URL.'))
    private_hash = models.CharField(editable=False, max_length=40, default='')
    public_hash = models.CharField(editable=False, max_length=40, default='')
    title = models.CharField(_('title'), max_length=255, blank=True, null=True)
    body = models.TextField(_('body'), help_text=_('Form description. Display on form after title.'), blank=True, null=True)
    action = models.URLField(_('target URL'), help_text=_('If you leave this empty, the page where the form resides will be requested, and you can use the mail form and logging features. You can also send data to external sites: For instance, enter "http://www.google.ch/search" to create a search form.'), max_length=255, blank=True, null=True)
    mail_to = TemplateCharField(_('send form data to e-mail address'), help_text=_('Separate several addresses with a comma. Your form fields are available as template context. Example: "admin@domain.com, {{ from_email }}" if you have a field named `from_email`.'), max_length=255, blank=True, null=True)
    mail_from = TemplateCharField(_('sender address'), max_length=255, help_text=MAIL_TEMPLATE_CONTEXT_HELP_TEXT, blank=True, null=True)
    mail_reply_to = TemplateCharField(_('reply-to address'), max_length=255, help_text=MAIL_TEMPLATE_CONTEXT_HELP_TEXT, blank=True)
    mail_subject = TemplateCharField(_('email subject'), max_length=255, help_text=_('Your form fields are available as template context. Example: "Contact form {{ subject }}" if you have a field named `subject`.'), blank=True, null=True)
    mail_uploaded_files = models.BooleanField(_('Send uploaded files as email attachments'), default=True)
    method = models.CharField(_('method'), max_length=10, default="POST", choices=(('POST', 'POST'), ('GET', 'GET')))
    success_message = models.CharField(_('success message'), max_length=255, blank=True, null=True)
    error_message = models.CharField(_('error message'), max_length=255, blank=True, null=True)
    submit_label = models.CharField(_('submit button label'), max_length=255, blank=True, null=True)
    log_data = models.BooleanField(_('log form data'), help_text=_('Logs all form submissions to the database.'), default=True)
    save_uploaded_files = models.BooleanField(_('save uploaded files'), help_text=_('Saves all uploaded files using server storage.'), default=True)
    success_redirect = models.BooleanField(_('HTTP redirect after successful submission'), default=True)
    success_clear = models.BooleanField(_('clear form after successful submission'), default=True)
    allow_get_initial = models.BooleanField(_('allow initial values via URL'), help_text=_('If enabled, you can fill in form fields by adding them to the query string.'), default=True)
    message_template = TemplateTextField(_('message template'), help_text=_('Your form fields are available as template context. Example: "{{ message }}" if you have a field named `message`. To iterate over all fields, use the variable `data` (a list containing a dictionary for each form field, each containing the elements `name`, `label`, `value`).'), blank=True, null=True)
    form_template_name = models.CharField(_('form template'), max_length=255, blank=True, null=True)
    display_logged = models.BooleanField(_('display logged submissions with form'), default=False)
    html_default_template = models.BooleanField(_('default email template in HTML'), default=False, help_text=_('If enabled, the default email template will be in HTML instead of plain format.'))

    class Meta:
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')

    def save(self, *args, **kwargs):
        if not self.private_hash:
            self.private_hash = get_random_hash()
        if not self.public_hash:
            self.public_hash = get_random_hash()
        super(FormDefinition, self).save()

    def get_field_dict(self):
        field_dict = OrderedDict()
        for field in self.formdefinitionfield_set.all():
            field_dict[field.name] = field
        return field_dict

    @models.permalink
    def get_absolute_url(self):
        if self.require_hash:
            return ('form_designer.views.detail_by_hash', [str(self.public_hash)])
        return ('form_designer.views.detail', [str(self.name)])

    def get_form_data(self, form):
        # TODO: refactor, move to utils or views
        data = []
        field_dict = self.get_field_dict()
        form_keys = form.fields.keys()
        def_keys = field_dict.keys()
        for key in form_keys:
            if key in def_keys and field_dict[key].include_result:
                value = form.cleaned_data[key]
                if getattr(value, '__form_data__', False):
                    value = value.__form_data__()
                data.append(FormValueDict(key, value, form.fields[key].label))
        return data

    def get_form_data_context(self, form_data):
        # TODO: refactor, move to utils
        dict = {}
        for field in form_data or ():
            dict[field['name']] = field['value']
        return dict

    def compile_message(self, form_data, template=None):
        # TODO: refactor, move to utils
        from django.template.loader import get_template
        from django.template import Template
        if template:
            t = get_template(template)
        elif not self.message_template:
            if self.html_default_template:
                template_file = 'html/formdefinition/data_table_message.html'
            else:
                template_file = 'txt/formdefinition/data_message.txt'
            t = get_template(template_file)
        else:
            t = Template(self.message_template)
        context = self.get_form_data_context(form_data)
        context['data'] = form_data
        if django.VERSION[:2] < (1, 8):
            from django.template import Context
            context = Context(context)
        return t.render(context)

    def count_fields(self):
        return self.formdefinitionfield_set.count()
    count_fields.short_description = _('Fields')

    def __str__(self):
        return self.title or self.name

    def log(self, form, user=None):
        form_data = self.get_form_data(form)
        created_by = None
        if user and user.is_authenticated():
            created_by = user
        flog = FormLog(form_definition=self, data=form_data, created_by=created_by)
        flog.save()
        return flog

    @warn_about_renamed_method(
        'FormDefinition', 'string_template_replace', 'form_designer.utils.string_template_replace',
        DeprecationWarning
    )
    def string_template_replace(self, text, context_dict):
        return string_template_replace(text, context_dict)

    def send_mail(self, form, files=None):
        if not self.mail_to:
            return
        from form_designer.email import build_form_mail
        message = build_form_mail(form_definition=self, form=form, files=files)
        message.send(fail_silently=False)
        return message

    @property
    def is_template_html(self):
        if (self.html_default_template and not self.message_template) or (
                    self.message_template and 
                    re.search(u"<[^>]+>", self.message_template) and
                    re.search(u"</[^>]+>", self.message_template)
                ):
            return True
        return False

    @property
    def submit_flag_name(self):
        name = settings.SUBMIT_FLAG_NAME % self.name
        # make sure we are not overriding one of the actual form fields
        while self.formdefinitionfield_set.filter(name__exact=name).count() > 0:
            name += '_'
        return name


@python_2_unicode_compatible
class FormDefinitionField(models.Model):

    form_definition = models.ForeignKey(FormDefinition)
    field_class = models.CharField(_('field class'), max_length=100)
    position = models.IntegerField(_('position'), blank=True, null=True)

    name = models.SlugField(_('name'), max_length=255)
    label = models.CharField(_('label'), max_length=255, blank=True, null=True)
    required = models.BooleanField(_('required'), default=True)
    include_result = models.BooleanField(_('include in result'), help_text=_('If this is disabled, the field value will not be included in logs and e-mails generated from form data.'), default=True)
    widget = models.CharField(_('widget'), default='', max_length=255, blank=True, null=True)
    initial = models.TextField(_('initial value'), blank=True, null=True)
    help_text = models.CharField(_('help text'), max_length=255, blank=True, null=True)

    choice_values = models.TextField(_('values'), help_text=_('One value per line'), blank=True, null=True)
    choice_labels = models.TextField(_('labels'), help_text=_('One label per line'), blank=True, null=True)

    max_length = models.IntegerField(_('max. length'), blank=True, null=True)
    min_length = models.IntegerField(_('min. length'), blank=True, null=True)
    max_value = models.FloatField(_('max. value'), blank=True, null=True)
    min_value = models.FloatField(_('min. value'), blank=True, null=True)
    max_digits = models.IntegerField(_('max. digits'), blank=True, null=True)
    decimal_places = models.IntegerField(_('decimal places'), blank=True, null=True)

    regex = RegexpExpressionField(_('regular Expression'), max_length=255, blank=True, null=True)

    choice_model = ModelNameField(_('data model'), max_length=255, blank=True, null=True)
    choice_model_empty_label = models.CharField(_('empty label'), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('field')
        verbose_name_plural = _('fields')
        ordering = ['position']

    def save(self, *args, **kwargs):
        if self.position is None:
            self.position = 0
        super(FormDefinitionField, self).save(*args, **kwargs)

    def get_form_field_init_args(self):
        args = {
            'required': self.required,
            'label': self.label if self.label else '',
            'initial': self.initial if self.initial else None,
            'help_text': self.help_text,
        }

        if self.field_class in ('django.forms.CharField', 'django.forms.EmailField', 'django.forms.RegexField'):
            args.update({
                'max_length': self.max_length,
                'min_length': self.min_length,
            })

        if self.field_class in ('django.forms.IntegerField', 'django.forms.DecimalField'):
            args.update({
                'max_value': int(self.max_value) if self.max_value is not None else None,
                'min_value': int(self.min_value) if self.min_value is not None else None,
            })

        if self.field_class == 'django.forms.DecimalField':
            args.update({
                'max_value': Decimal(str(self.max_value)) if self.max_value is not None else None,
                'min_value': Decimal(str(self.min_value)) if self.max_value is not None else None,
                'max_digits': self.max_digits,
                'decimal_places': self.decimal_places,
            })

        if self.field_class == 'django.forms.RegexField':
            if self.regex:
                args.update({
                    'regex': self.regex
                })

        if self.field_class in ('django.forms.ChoiceField', 'django.forms.MultipleChoiceField'):
            if self.choice_values:
                choices = []
                regex = re.compile('[\s]*\n[\s]*')
                values = regex.split(self.choice_values)
                labels = regex.split(self.choice_labels) if self.choice_labels else []
                for index, value in enumerate(values):
                    try:
                        label = labels[index]
                    except:
                        label = value
                    choices.append((value, label))
                args.update({
                    'choices': tuple(choices)
                })

        if self.field_class in ('django.forms.ModelChoiceField', 'django.forms.ModelMultipleChoiceField'):
            args.update({
                'queryset': ModelNameField.get_model_from_string(self.choice_model).objects.all()
            })

        if self.field_class == 'django.forms.ModelChoiceField':
            args.update({
                'empty_label': self.choice_model_empty_label
            })

        if self.widget:
            args.update({
                'widget': import_string(self.widget)()
            })

        return args

    def __str__(self):
        return (self.label or self.name)


@python_2_unicode_compatible
class FormLog(models.Model):
    form_definition = models.ForeignKey(FormDefinition, related_name='logs')
    created = models.DateTimeField(_('Created'), auto_now=True)
    created_by = models.ForeignKey(getattr(django_settings, "AUTH_USER_MODEL", "auth.User"), null=True, blank=True)
    _data = None

    class Meta:
        verbose_name = _('form log')
        verbose_name_plural = _('form logs')

    def __str__(self):
        return "%s (%s)" % (
            self.form_definition.title or self.form_definition.name,
            self.created
        )

    def get_data(self):
        if self._data:
            # before instance is saved
            return self._data
        data = []
        fields = self.form_definition.get_field_dict()
        values_with_header = {}
        values_without_header = []
        for item in self.values.all():
            field = fields.get(item.field_name, None)
            if field:
                # get field label if field definition still exists
                label = field.label
            else:
                # field may have been removed
                label = None

            value_dict = FormValueDict(item.field_name, item.value,
                                       label)

            if item.field_name in fields:
                values_with_header[item.field_name] = value_dict
            else:
                values_without_header.append(value_dict)

        for field_name, field in fields.items():
            if field_name in values_with_header:
                data.append(values_with_header[field_name])
            else:
                data.append(FormValueDict(field.name, None, field.label))
        for value in values_without_header:
            data.append(value)

        return data

    def set_data(self, form_data):
        # keep form data in temporary variable since instance must
        # be saved before saving values
        self._data = form_data

    data = property(get_data, set_data)

    def save(self, *args, **kwargs):
        super(FormLog, self).save(*args, **kwargs)
        if self._data:
            # safe form data and then clear temporary variable
            for value in self.values.all():
                value.delete()
            for item in self._data:
                FormValue.objects.create(
                    form_log=self,
                    field_name=item['name'],
                    value=item['value'],
                )
            self._data = None


@python_2_unicode_compatible
class FormValue(models.Model):
    form_log = models.ForeignKey(FormLog, related_name='values')
    field_name = models.SlugField(_('field name'), max_length=255)
    value = PickledObjectField(_('value'), null=True, blank=True)

    def __str__(self):
        return u'%s = %s' % (self.field_name, self.value)
