"""
User module. Meant to manage registering, login, email confirmation, password
resets,..."""

from django.apps import AppConfig


class UserConfig(AppConfig):
    """Configuration of the User Django App"""
    name = "insalan.user"
    verbose_name = "User Management Application"
    default_auto_field = "django.db.models.BigAutoField"
