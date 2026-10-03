from django.apps import apps


def test_learning_sessions_app_is_installed():
    assert apps.is_installed("apps.learning_sessions")
