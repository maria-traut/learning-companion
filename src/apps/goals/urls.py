from django.urls import path

from .views import (
    GoalCreateView,
    GoalDeleteView,
    GoalDetailView,
    GoalListView,
    GoalUpdateView,
)

app_name = "goals"

urlpatterns = [
    path("", GoalListView.as_view(), name="list"),
    path("new/", GoalCreateView.as_view(), name="create"),
    path("<int:pk>/", GoalDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", GoalUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", GoalDeleteView.as_view(), name="delete"),
]
