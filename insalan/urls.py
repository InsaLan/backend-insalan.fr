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
from os import getenv

from django.urls import re_path
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import include, path
from rest_framework import routers
from rest_framework import permissions

from insalan.mailer import start_job
from . import scheduler
from insalan.langate import views as langate_views


router = routers.DefaultRouter()
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("v1/", include(router.urls)),
    path("v1/partners/", include("insalan.partner.urls")),
    path("v1/tournament/", include("insalan.tournament.urls")),
    path("v1/user/", include("insalan.user.urls")),
    path("v1/tickets/", include("insalan.tickets.urls")),
    path("v1/langate/authenticate/", langate_views.LangateUserView.as_view()),
    path("v1/content/", include("insalan.cms.urls")),
    path("v1/admin/", admin.site.urls),
    path("v1/payment/", include("insalan.payment.urls")),
    path("v1/pizza/", include("insalan.pizza.urls")),
]
if getenv("DEV", "1") == "1":
    from drf_yasg.views import get_schema_view  # type: ignore[import]
    from drf_yasg import openapi  # type: ignore[import]

    SchemaView = get_schema_view(
        openapi.Info(
            title="InsaLAN API",
            default_version='v1',
            # pylint: disable-next=line-too-long
            description="Cette API est l'API privée de l'INSALAN. Elle est utilisée pour gérer les inscriptions, les tournois, les partenaires, les utilisateurs, les tickets et le contenu du site l'INSALAN.",
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )

    urlpatterns += [
        re_path(r'^v1/swagger(?P<format>\.json|\.yaml)$', SchemaView.without_ui(cache_timeout=0),
                name='schema-json'),
        path("v1/swagger/", SchemaView.with_ui('swagger', cache_timeout=0),
             name='schema-swagger-ui'),
        path("v1/redoc/", SchemaView.with_ui('redoc', cache_timeout=0), name='schema-redoc-ui'),
    ]

if not int(getenv("DEV", "1")):
    urlpatterns.insert(1,
        path("v1/admin/login/", RedirectView.as_view(
            url=f"{getenv('HTTP_PROTOCOL')}://{getenv('WEBSITE_HOST')}/register"
        )))

# Set admin site url correctly for the admin panel
admin.site.site_url = getenv("HTTP_PROTOCOL", "http") + "://" + getenv("WEBSITE_HOST", "localhost")

scheduler.start()
start_job()
