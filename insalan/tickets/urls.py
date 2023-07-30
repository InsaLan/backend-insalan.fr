from django.urls import path

from . import views


app_name = 'tickets'
urlpatterns = [
    path('get/<str:username>/<str:token>', views.get, name='get'),
    path('scan/<str:token>', views.scan, name='scan'),
    path('qrcode/<str:token>', views.qrcode, name='qrcode'),
]
