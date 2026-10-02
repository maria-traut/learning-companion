from django.urls import path

from .views import GoalCreateView, GoalListView

app_name = "goals"

urlpatterns = [
    path("", GoalListView.as_view(), name="list"),
    path("new/", GoalCreateView.as_view(), name="create"),
]
