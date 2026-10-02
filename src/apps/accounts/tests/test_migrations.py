import importlib

import pytest
from django.apps import apps
from django.db import migrations

from apps.accounts.models import Profile

PASSWORD = "correct-horse-battery-9"

backfill_migration = importlib.import_module("apps.accounts.migrations.0002_backfill_profiles")


def test_backfill_migration_runs_backfill_profiles():
    operation = backfill_migration.Migration.operations[0]

    assert isinstance(operation, migrations.RunPython)
    assert operation.code is backfill_migration.backfill_profiles


@pytest.mark.django_db
def test_backfill_creates_missing_profiles_and_leaves_existing_ones_unchanged(django_user_model):
    ada = django_user_model.objects.create_user(username="ada", password=PASSWORD)
    ada.profile.delete()
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    grace.profile.name = "Grace Hopper"
    grace.profile.save()
    graces_profile_pk = grace.profile.pk

    backfill_migration.backfill_profiles(apps, None)
    backfill_migration.backfill_profiles(apps, None)

    assert Profile.objects.filter(user=ada).count() == 1
    graces_profile = Profile.objects.get(user=grace)
    assert graces_profile.pk == graces_profile_pk
    assert graces_profile.name == "Grace Hopper"
    assert Profile.objects.count() == 2
