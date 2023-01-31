from django.db import models
from django.db.contrib.auth.models import User


class InsalanUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.cascade)
