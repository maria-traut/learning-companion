from django.contrib.auth.views import LoginView
from django.urls import path

from .views import SignUpView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
]
