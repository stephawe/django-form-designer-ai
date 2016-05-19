import pytest


@pytest.mark.django_db
def test_admin_list_view_renders(admin_client):
    assert admin_client.get("/admin/form_designer/formdefinition/").content

@pytest.mark.django_db
def test_admin_create_view_renders(admin_client):
    assert admin_client.get("/admin/form_designer/formdefinition/add/").content
