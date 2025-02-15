"""URLs for tournament"""
from django.urls import path

from . import views

urlpatterns = [
    path("event/", views.EventList.as_view(), name="event/list"),
    path("event/ongoing/", views.OngoingEventList.as_view(), name="event/ongoing"),
    path("event/<int:pk>/", views.EventDetails.as_view(), name="event/details"),
    path(
        "event/<int:primary_key>/tournaments/",
        views.EventDetailsSomeDeref.as_view(),
        name="event/details-tournaments",
    ),
    path("event/year/<int:year>/", views.EventByYear.as_view(), name="event/by-year"),
    path("game/", views.GameList.as_view(), name="game/list"),
    path("game/<int:pk>/", views.GameDetails.as_view(), name="game/details"),
    path("tournament/", views.TournamentList.as_view(), name="tournament/list"),
    path(
        "tournament/<int:pk>/",
        views.TournamentDetails.as_view(),
        name="tournament/details/",
    ),
    path(
        "tournament/<int:primary_key>/full/",
        views.TournamentDetailsFull.as_view(),
        name="tournament/details-full",
    ),
    path("me/", views.TournamentMe.as_view(), name="tournament/me"),
    path("team/", views.TeamList.as_view(), name="team/list"),
    path("team/<int:pk>/", views.TeamDetails.as_view(), name="team/details"),
    path("team/<int:pk>/matchs", views.TeamMatchs.as_view(), name="team/matchs"),
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
    path("substitute/", views.SubstituteRegistrationList.as_view(), name="substitute/list"),
    path(
        "substitute/<int:pk>/", views.SubstituteRegistration.as_view(), name="substitute/details"
    ),
    path(
        "substitute/fromUserId/<int:user_id>/",
        views.SubstituteRegistrationListId.as_view(),
        name="substitute/listFromUserId",
    ),
    path(
        "substitute/fromUsername/<str:username>/",
        views.SubstituteRegistrationListName.as_view(),
        name="substitute/listFromUsername",
    ),
    # path(
    #     "group/",
    #     views.GroupList.as_view(),
    #     name="group/list"
    # ),
    path(
        "group/<int:group_id>/match/<int:match_id>/",
        views.GroupMatchScore.as_view(),
        name="group/match/score"
    ),
    # path(
    #     "bracket/"
    # ),
    path(
        "bracket/<int:bracket_id>/match/<int:match_id>/",
        views.BracketMatchScore.as_view(),
        name="bracket/match/score"
    ),
    # path(
    #     "match/"
    # ),
    path(
        "swiss/<int:swiss_id>/match/<int:match_id>/",
        views.SwissMatchScore.as_view(),
        name="swiss/match/score"
    ),
]
