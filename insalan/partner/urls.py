from django.urls import path

from . import views


app_name = 'partners'
urlpatterns = [
    path('', views.PartnerList.as_view(), name='list'),
    path('<int:pk>/', views.PartnerDetail.as_view(), name='detail'),
]
