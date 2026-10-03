from django.core.validators import MinValueValidator
from django.db import models

from apps.goals.models import Goal


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LearningSession(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.goal.title} – {self.date:%Y-%m-%d} ({self.duration_minutes} min)"
