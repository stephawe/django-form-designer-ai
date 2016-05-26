from django.contrib.auth.models import AnonymousUser
from django.utils.crypto import get_random_string

import pytest
from cms import api
from cms.page_rendering import render_page
from form_designer.contrib.cms_plugins.form_designer_form.cms_plugins import FormDesignerPlugin
from form_designer.models import FormDefinition, FormDefinitionField


@pytest.mark.django_db
def test_cms_plugin_renders_in_cms_page(rf):
    fd = FormDefinition.objects.create(
        mail_to='test@example.com',
        mail_subject='Someone sent you a greeting: {{ test }}'
    )
    field = FormDefinitionField.objects.create(
        form_definition=fd,
        name='test',
        label=get_random_string(),
        field_class='django.forms.CharField',
    )
    page = api.create_page("test", "page.html", "en")
    ph = page.get_placeholders()[0]
    api.add_plugin(ph, FormDesignerPlugin, "en", form_definition=fd)
    request = rf.get("/")
    request.user = AnonymousUser()
    request.current_page = page
    response = render_page(request, page, "fi", "test")
    response.render()
    content = response.content.decode("utf8")
    assert field.label in content
    assert "<form" in content
