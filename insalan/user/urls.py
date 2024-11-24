"""url for user"""
from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.UserRegister.as_view(), name="/register"),
    path("login/", views.UserLogin.as_view(), name="/login"),
    path("logout/", views.UserLogout.as_view(), name="/logout"),
    path("data/<int:pk>/", views.UserView.as_view(), name="/"),
    path("me/", views.UserMe.as_view(), name="me"),
    path(
        "resend-email/", views.ResendEmailConfirmView.as_view(), name="resend-confirm"
    ),
    path("get-csrf/", views.get_csrf, name="get-csrf"),
    path(
        "confirm/<int:pk>/<str:token>/",
        views.EmailConfirmView.as_view(),
        name="confirm-email",
    ),
    path(
        "password-reset/ask/",
        views.AskForPasswordReset.as_view(),
        name="ask-for-password",
    ),
    path(
        "password-reset/submit/", views.ResetPassword.as_view(), name="reset-password"
    ),
]
