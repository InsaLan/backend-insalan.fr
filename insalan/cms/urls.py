from django.urls import path
from . import views

urlpatterns = [
    path("constant/", views.ConstantList.as_view(), name="constant/list"),
    path("constant/<str:name>", views.ConstantFetch.as_view(), name="constant/name"),
    path("content/<str:section>/", views.ContentFetch.as_view(), name="content/section")
]
