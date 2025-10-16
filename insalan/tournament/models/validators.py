from collections import Counter
from math import ceil

from django.utils.translation import gettext_lazy as _
from rest_framework.validators import ValidationError

from insalan.user.models import User

# from .event import Event
from . import tournament
from . import team
from . import player as play
from . import manager as manage
from . import substitute as sub
from . import match as Match
from . import game

def unique_event_registration_validator(user: User, event: "Event", player = None, manager = None, substitute = None):
    """Validate a unique registration per event"""
    player_regs = play.Player.objects.filter(user=user).exclude(id=player)

    for reg in player_regs:
        if isinstance(reg.get_team().get_tournament(), tournament.EventTournament) and reg.get_team().get_tournament().get_event().id == event.id:
            return False

    manager_regs = manage.Manager.objects.filter(user=user).exclude(id=manager)

    for reg in manager_regs:
        if isinstance(reg.get_team().get_tournament(), tournament.EventTournament) and reg.get_team().get_tournament().get_event().id == event.id:
            return False

    substitute_regs = sub.Substitute.objects.filter(user=user).exclude(id=substitute)
    for reg in substitute_regs:
        if isinstance(reg.get_team().get_tournament(), tournament.EventTournament) and reg.get_team().get_tournament().get_event().id == event.id:
            return False

    return True

def player_manager_user_unique_validator(user: User):
    """
    Validate that a user cannot be a player and manager of the same
    tournament
    """
    p_regs = {
        (obj.user, obj.team.tournament) for obj in play.Player.objects.filter(user=user)
    }
    m_regs = {
        (obj.user, obj.team.tournament) for obj in manage.Manager.objects.filter(user=user)
    }
    s_regs = {
        (obj.user, obj.team.tournament) for obj in sub.Substitute.objects.filter(user=user)
    }
    if len(m_regs.intersection(p_regs)) > 0 or len(s_regs.intersection(p_regs)) > 0 or len(s_regs.intersection(m_regs)) > 0:
        raise ValidationError(
            _("Utilisateur⋅rice déjà inscrit⋅e dans ce tournois (rôles distincts)")
        )

def max_players_per_team_reached(team: "Team", exclude=None):
    """Validate the number of players in a team"""
    if len(team.get_players().exclude(id=exclude)) >= team.get_tournament().get_game().get_players_per_team():
        return True
    return False

def max_substitue_per_team_reached(team: "Team", exclude=None):
    """Validate the number of sub in a team"""
    if len(team.get_substitutes().exclude(id=exclude)) >= team.get_tournament().get_game().get_substitute_players_per_team():
        return True
    return False

def tournament_announced(tourney: "BaseTournament"):
    """Validate if a tournament is announced"""
    if isinstance(tourney, tournament.PrivateTournament) or tourney.is_announced:
        return True
    return False

def tournament_registration_full(tourney: "BaseTournament", exclude=None):
    """Validate if a tournament is full"""
    if exclude is not None:
        return False
    if tourney.get_validated_teams(exclude) >= tourney.get_max_team():
        return True
    return False

def private_tournament_password_matching(tourney: "BaseTournament", password: str):
    """Validate the password of a private tournament"""
    if isinstance(tourney, tournament.PrivateTournament):
        return tourney.password is None or tourney.password == password
    return True

def validate_match_data(match: "Match", data):
    winning_score = match.get_winning_score()
    winner_count = 0
    max_score = match.get_max_score()

    if Counter(map(int,data["score"].keys())) != Counter(match.get_teams_id()):
        return {
            "teams" : "Liste des équipes invalide"
        }

    if sum(data["score"].values()) > match.get_total_max_score():
        return {
            "score" : "Les scores sont invalides, le score total cummulé est trop grand"
        }

    for score in data["score"].values():
        if score > max_score:
            return {
                "score" : "Le score d'une équipe est trop grand"
            }

        if score < 0:
            return {
                "score": "Le score d'une équipe ne peut pas être négatif."
            }

        if match.bo_type == Match.BestofType.RANKING and score <= winning_score:
            winner_count += 1
        elif match.bo_type != Match.BestofType.RANKING and score >= winning_score:
            winner_count += 1

    if (
        (match.bo_type == Match.BestofType.RANKING and winner_count != ceil(match.get_team_count()/2)) 
        or
        (match.bo_type != Match.BestofType.RANKING and winner_count != 1)
    ) :
        return {
            "score": "Scores incomplets, il y a trop ou pas assez de gagnants."
        }

    return None

def valid_name(game_param: "game", name: str):
    name_validator = game_param.get_name_validator()
    if name_validator is None:
        return True
    return name_validator(name)
