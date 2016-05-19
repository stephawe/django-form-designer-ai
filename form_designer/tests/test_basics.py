import pytest

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile, File

from form_designer.models import FormDefinition, FormDefinitionField, FormLog
from form_designer.views import process_form


@pytest.mark.django_db
def test_simple_form(rf):
    fd = FormDefinition.objects.create()
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
    request = rf.post('/', {
        'test': 'Hello, world!',
        'upload': ContentFile('hello!', name='hello.txt'),
        fd.submit_flag_name: 'true',
    })
    request.user = AnonymousUser()
    process_form(request, fd, push_messages=False)
    flog = FormLog.objects.get(form_definition=fd)
    name_to_value = {d['name']: d['value'] for d in flog.data}
    assert name_to_value['test'] == 'Hello, world!'
    assert isinstance(name_to_value['upload'], File)
