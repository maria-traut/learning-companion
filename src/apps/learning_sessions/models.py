from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.goals.models import Goal


def validate_not_in_future(value):
    if value > timezone.localdate():
        raise ValidationError("The date cannot be in the future.", code="future_date")


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LearningSession(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField(default=timezone.localdate, validators=[validate_not_in_future])
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, related_name="sessions")

    def __str__(self):
        return f"{self.goal.title} – {self.date:%Y-%m-%d} ({self.duration_minutes} min)"
