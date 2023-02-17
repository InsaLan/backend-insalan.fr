from django.urls import include, path

from . import views


urlpatterns = [
    path('', views.PartnerList.as_view()),
    path('<int:pk>/', views.PartnerDetail.as_view()),
]
