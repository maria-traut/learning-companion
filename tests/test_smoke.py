from django.core.management import call_command


def test_django_system_checks_pass():
    call_command("check", fail_level="WARNING")


def test_admin_login_page_is_served(client):
    response = client.get("/admin/login/")

    assert response.status_code == 200
