from django.contrib.auth.models import User


class InsalanUser(User):
    class Meta:
        proxy = True
