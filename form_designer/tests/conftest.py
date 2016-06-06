import pytest


@pytest.fixture()
def greeting_form():
    from form_designer.models import FormDefinition, FormDefinitionField
    fd = FormDefinition.objects.create(
        mail_to='test@example.com',
        mail_subject='Someone sent you a greeting: {{ greeting }}',
        mail_reply_to='Greeting Bot <greetingbot@example.com>',
    )
    FormDefinitionField.objects.create(
        form_definition=fd,
        name='greeting',
        label='Greeting',
        field_class='django.forms.CharField',
        required=True,
    )
    FormDefinitionField.objects.create(
        form_definition=fd,
        name='upload',
        field_class='django.forms.FileField',
        required=False,
    )
    return fd
