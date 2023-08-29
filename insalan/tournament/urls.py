"""URLs for tournament"""
from django.urls import path

from . import views

urlpatterns = [
    path("event/", views.EventList.as_view(), name="event/list"),
    path("event/ongoing/", views.OngoingEventList.as_view(), name="event/ongoing"),
    path("event/<int:pk>/", views.EventDetails.as_view(), name="event/details"),
    path("game/", views.GameList.as_view(), name="game/list"),
    path("game/<int:pk>/", views.GameDetails.as_view(), name="game/details"),
    path("tournament/", views.TournamentList.as_view(), name="tournament/list"),
    path(
        "tournament/<int:pk>/",
        views.TournamentDetails.as_view(),
        name="tournament/details",
    ),
    path("team/", views.TeamList.as_view(), name="team/list"),
    path("team/<int:pk>/", views.TeamDetails.as_view(), name="team/details"),
    path("player/", views.PlayerRegistrationList.as_view(), name="player/list"),
    path("player/<int:pk>/", views.PlayerRegistration.as_view(), name="player/details"),
    path(
        "player/fromUserId/<int:user_id>/",
        views.PlayerRegistrationListId.as_view(),
        name="player/listFromUserId",
    ),
    path(
        "player/fromUsername/<str:username>/",
        views.PlayerRegistrationListName.as_view(),
        name="player/listFromUsername",
    ),
    path("manager/", views.ManagerRegistrationList.as_view(), name="manager/list"),
    path(
        "manager/<int:pk>/", views.ManagerRegistration.as_view(), name="manager/details"
    ),
    path(
        "manager/fromUserId/<int:user_id>/",
        views.ManagerRegistrationListId.as_view(),
        name="manager/listFromUserId",
    ),
    path(
        "manager/fromUsername/<str:username>/",
        views.ManagerRegistrationListName.as_view(),
        name="manager/listFromUsername",
    ),
]
