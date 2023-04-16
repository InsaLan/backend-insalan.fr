from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'insalan.user'
    verbose_name = 'User Management Application'
    default_auto_field = 'django.db.models.BigAutoField'
