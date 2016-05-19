from base64 import b64decode

import pytest

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.files.base import ContentFile, File
from django.utils.crypto import get_random_string

from form_designer.contrib.exporters.csv_exporter import CsvExporter
from form_designer.models import FormDefinition, FormDefinitionField, FormLog
from form_designer.views import process_form

# https://raw.githubusercontent.com/mathiasbynens/small/master/jpeg.jpg

VERY_SMALL_JPEG = b64decode(
    '/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgK'
    'CgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/'
    'yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k='
)

@pytest.mark.django_db
def test_simple_form(rf):
    fd = FormDefinition.objects.create(
        mail_to='test@example.com',
        mail_subject='Someone sent you a greeting: {{ test }}'
    )
    FormDefinitionField.objects.create(
        form_definition=fd,
        name='test',
        label='Greeting',
        field_class='django.forms.CharField',
    )
    FormDefinitionField.objects.create(
        form_definition=fd,
        name='upload',
        field_class='django.forms.FileField',
    )
    message = get_random_string()
    request = rf.post('/', {
        'test': message,
        'upload': ContentFile(VERY_SMALL_JPEG, name='hello.jpg'),
        fd.submit_flag_name: 'true',
    })
    request.user = AnonymousUser()
    process_form(request, fd, push_messages=False)

    # Test that the form log was saved:
    flog = FormLog.objects.get(form_definition=fd)
    name_to_value = {d['name']: d['value'] for d in flog.data}
    assert name_to_value['test'] == message
    assert isinstance(name_to_value['upload'], File)

    # Test that the email was sent:
    assert message in mail.outbox[-1].subject

    # TODO: Improve CSV test
    csv_data = CsvExporter(fd).export(
        request=rf.get("/"),
        queryset=FormLog.objects.filter(form_definition=fd)
    ).content.decode("utf8").splitlines()
    assert csv_data[0].startswith("Created")
    assert "Greeting" in csv_data[0]
    assert message in csv_data[1]
