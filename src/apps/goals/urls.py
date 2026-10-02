from django.urls import path

from .views import GoalListView

app_name = "goals"

urlpatterns = [
    path("", GoalListView.as_view(), name="list"),
]
