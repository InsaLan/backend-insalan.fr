"""insalan URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib import admin

from rest_framework import routers

from insalan.user import views as user_views
from insalan.langate import views as langate_views

router = routers.DefaultRouter()
router.register(r'users', user_views.UserViewSet)
router.register(r'permissions', user_views.PermissionViewSet)
router.register(r'groups', user_views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/partners/', include('insalan.partner.urls')),
    path('v1/user/register/', user_views.UserRegister.as_view()),
    path('v1/langate/authenticate', langate_views.LangateUserView.as_view()),

    path('v1/api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
    path('v1/admin/', admin.site.urls),

]

# Set admin site url correctly for the admin panel
admin.site.site_url = '/v1/'
