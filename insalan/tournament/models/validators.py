from insalan.user.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework.validators import ValidationError
from django.core.exceptions import BadRequest

# from .event import Event
from . import player as play
from . import manager as manage
from . import substitute as sub
from . import match as Match

def unique_event_registration_validator(user: User, event: "Event", player = None, manager = None, substitute = None):
    """Validate a unique registration per event"""
    e_regs = play.Player.objects.filter(team__tournament__event=event,user=user).exclude(id=player).values("id").union(manage.Manager.objects.filter(team__tournament__event=event, user=user).exclude(id=manager).values("id")).union(sub.Substitute.objects.filter(team__tournament__event=event, user=user).exclude(id=substitute).values("id"))
    if len(e_regs) > 0:
        return False
    return True

def player_manager_user_unique_validator(user: User):
    """
    Validate that a user cannot be a player and manager of the same
    tournament
    """
    p_regs = {
        (obj.user, obj.team.tournament) for obj in player.Player.objects.filter(user=user)
    }
    m_regs = {
        (obj.user, obj.team.tournament) for obj in manager.Manager.objects.filter(user=user)
    }
    s_regs = {
        (obj.user, obj.team.tournament) for obj in substitute.Substitute.objects.filter(user=user)
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

def tournament_announced(tournament: "Tournament"):
    """Validate if a tournament is announced"""
    if tournament.is_announced:
        return True
    return False

def tournament_registration_full(tournament: "Tournament", exclude=None):
    """Validate if a tournament is full"""
    if tournament.get_validated_teams(exclude) >= tournament.get_max_team():
        return True
    return False

def validate_match_data(match: "Match", data):
    if match.status != Match.MatchStatus.ONGOING:
        raise BadRequest(_("Le match n'est pas en cours"))

    if match.round_number != data["round_number"]:
        raise BadRequest(_("Mauvais numéro de round"))

    if match.index_in_round != data["index_in_round"]:
        raise BadRequest(_("Mauvais index du match dans le round"))

    if Counter(map(int,data["score"].keys())) != Counter(match.get_teams_id()) or Counter(data["teams"]) != Counter(match.get_teams_id()):
        raise BadRequest(_("Liste des équipes invalide"))

    if sum(data["score"].values()) > match.get_total_max_score():
        raise BadRequest(_("Les scores sont invalides, le score total cummulé est trop grand"))

    for _,score in data["score"].items():
        if score > match.get_max_score():
            raise BadRequest(_("Le score d'une équipe est trop grand"))