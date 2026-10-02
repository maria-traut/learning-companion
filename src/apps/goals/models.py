from django.conf import settings
from django.db import models


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals"
    )
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title
