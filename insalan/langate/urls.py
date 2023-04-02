from django.urls import path

from . import views


app_name = 'pizza'
urlpatterns = [
    path('2me', views.LangateUserViewSet, name='langate_auth'),
]
