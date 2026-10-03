import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_learning_sessions_has_no_pending_migrations():
    call_command("makemigrations", "learning_sessions", "--check", "--dry-run", verbosity=0)
