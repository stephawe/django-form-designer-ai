# -- encoding: UTF-8 --
from __future__ import unicode_literals
from base64 import b64decode

import pytest

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.files.base import ContentFile, File
from django.utils.crypto import get_random_string
from form_designer.contrib.exporters.xls_exporter import XlsExporter
from form_designer.contrib.exporters.csv_exporter import CsvExporter
from form_designer.models import FormDefinition, FormDefinitionField, FormLog, FormValue
from form_designer.views import process_form

# https://raw.githubusercontent.com/mathiasbynens/small/master/jpeg.jpg

VERY_SMALL_JPEG = b64decode(
    '/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgK'
    'CgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/'
    'yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k='
)


@pytest.mark.django_db
def test_simple_form(rf, greeting_form):
    fd = greeting_form
    message = 'å%sÖ' % get_random_string()
    request = rf.post('/', {
        'greeting': message,
        'upload': ContentFile(VERY_SMALL_JPEG, name='hello.jpg'),
        fd.submit_flag_name: 'true',
    })
    request.user = AnonymousUser()
    process_form(request, fd, push_messages=False)

    # Test that the form log was saved:
    flog = FormLog.objects.get(form_definition=fd)
    name_to_value = {d['name']: d['value'] for d in flog.data}
    assert name_to_value['greeting'] == message
    assert isinstance(name_to_value['upload'], File)

    # Test that the email was sent:
    assert message in mail.outbox[-1].subject


@pytest.mark.django_db
@pytest.mark.parametrize('exporter', [
    CsvExporter,
    XlsExporter,
])
@pytest.mark.parametrize('n_logs', range(5))
def test_export(rf, greeting_form, exporter, n_logs):
    message = u'Térve'
    for n in range(n_logs):
        fl = FormLog.objects.create(
            form_definition=greeting_form
        )
        FormValue.objects.create(
            form_log=fl,
            field_name='greeting',
            value="%s %d" % (message, n + 1),
        )

    resp = exporter(greeting_form).export(
        request=rf.get("/"),
        queryset=FormLog.objects.filter(form_definition=greeting_form)
    )
    if 'csv' in resp['content-type']:
        # TODO: Improve CSV test?
        csv_data = resp.content.decode("utf8").splitlines()
        if n_logs > 0:  # The file will be empty if no logs exist
            assert csv_data[0].startswith("Created")
            assert "Greeting" in csv_data[0]
            for i in range(1, n_logs):
                assert message in csv_data[i]
                assert ("%s" % i) in csv_data[i]
