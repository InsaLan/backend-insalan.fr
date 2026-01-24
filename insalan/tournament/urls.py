"""URLs for tournament"""
from django.urls import path

from . import views

urlpatterns = [
    path("event/", views.EventList.as_view(), name="event/list"),
    path("event/ongoing/", views.OngoingEventList.as_view(), name="event/ongoing"),
    path("event/<int:pk>/", views.EventDetails.as_view(), name="event/details"),
    path(
        "event/<int:pk>/tournaments/",
        views.EventDetailsSomeDeref.as_view(),
        name="event/details-tournaments",
    ),
    path("event/year/<int:year>/", views.EventByYear.as_view(), name="event/by-year"),
    path("game/", views.GameList.as_view(), name="game/list"),
    path("game/<int:pk>/", views.GameDetails.as_view(), name="game/details"),
    path(
        "tournament/privates/",
        views.PrivateTournamentList.as_view(),
        name="private-tournament/list"
    ),
    path(
        "tournament/privates/<int:pk>/",
        views.PrivateTournamentDetails.as_view(),
        name="private-tournament/details"
    ),
    path("tournament/", views.TournamentList.as_view(), name="tournament/list"),
    path(
        "tournament/<int:pk>/",
        views.TournamentDetails.as_view(),
        name="tournament/details/",
    ),
    path(
        "tournament/<int:pk>/full/",
        views.TournamentDetailsFull.as_view(),
        name="tournament/details-full",
    ),
    path("me/", views.TournamentMe.as_view(), name="tournament/me"),
    path("team/", views.TeamList.as_view(), name="team/list"),
    path("team/seeding", views.AdminTeamSeeding.as_view(), name="team/seeding"),
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
    path(
        "group/",
        views.GroupList.as_view(),
        name="group/list"
    ),
    path(
        "group/<int:pk>/",
        views.GroupDetails.as_view(),
        name="group/details"
    ),
    path(
        "group/<int:group_id>/match/<int:match_id>/",
        views.GroupMatchPatch.as_view(),
        name="group/match"
    ),
    path(
        "group/<int:group_id>/match/<int:match_id>/score/",
        views.GroupMatchScore.as_view(),
        name="group/match/score"
    ),
    path(
        "groups/delete/",
        views.GroupsDelete.as_view(),
        name="groups/delete"
    ),
    path(
        "groups/matchs/create/",
        views.GroupsMatchsCreate.as_view(),
        name="groups/matchs/create"
    ),
    path(
        "groups/matchs/launch/",
        views.GroupsMatchsLaunch.as_view(),
        name="groupe/matchs/launch"
    ),
    path(
        "groups/matchs/delete/",
        views.GroupsMatchsDelete.as_view(),
        name="groups/matchs/delete"
    ),
    path(
        "bracket/<int:pk>/",
        views.BracketDetails.as_view(),
        name="bracket/details"
    ),
    path(
        "bracket/<int:bracket_id>/match/<int:match_id>/",
        views.BracketMatchPatch.as_view(),
        name="bracket/match"
    ),
    path(
        "bracket/<int:bracket_id>/match/<int:match_id>/score/",
        views.BracketMatchScore.as_view(),
        name="bracket/match/score"
    ),
    path(
        "brackets/matchs/launch/",
        views.BracketMatchsLaunch.as_view(),
        name="bracket/matchs/launch"
    ),
    path(
        "swiss/<int:pk>/",
        views.SwissRoundsDetails.as_view(),
        name="swiss/details"
    ),
    path(
        "swiss/<int:pk>/fill_round/",
        views.SwissFillRound.as_view(),
        name="swiss/fill_round"
    ),
    path(
        "swiss/<int:swiss_id>/match/<int:match_id>/",
        views.SwissMatchPatch.as_view(),
        name="swiss/match"
    ),
    path(
        "swiss/<int:swiss_id>/match/<int:match_id>/score/",
        views.SwissMatchScore.as_view(),
        name="swiss/match/score"
    ),
    path(
        "swiss/matchs/launch/",
        views.SwissMatchsLaunch.as_view(),
        name="swiss/matchs/launch"
    ),
	path(
		"stage/create/",
		views.CreateStage.as_view(),
		name="create/stage"
    ),
	path(
        "stage/<int:pk>/update/",
		views.UpdateStage.as_view(),
		name="update/stage"
    ),
	path(
		"stage/<int:pk>/delete/",
		views.DeleteStage.as_view(),
		name="delete/stage"
    ),
    path(
        "stage/<int:pk>/add/groups/",
        views.StageAddGroups.as_view(),
        name="stage/add/groups"
    ),
    path(
        "stage/<int:pk>/add/bracket/",
        views.StageAddBracket.as_view(),
        name="stage/add/bracket"
    ),
    path(
        "stage/<int:pk>/add/swiss/",
        views.StageAddSwissRounds.as_view(),
        name="stage/add/swiss"
    )
]
