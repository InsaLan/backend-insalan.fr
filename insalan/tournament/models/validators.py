from insalan.user.models import User

from .event import Event
from .player import Player
from .manager import Manager
from .substitute import Substitute
from .team import Team
from .tournament import Tournament

def unique_event_registration_validator(user: User, event: Event, player = None, manager = None, substitute = None):
    """Validate a unique registration per event"""
    e_regs = Player.objects.filter(team__tournament__event=event,user=user).exclude(id=player).values("id").union(Manager.objects.filter(team__tournament__event=event, user=user).exclude(id=manager).values("id")).union(Substitute.objects.filter(team__tournament__event=event, user=user).exclude(id=substitute).values("id"))
    if len(e_regs) > 0:
        return False
    return True

def player_manager_user_unique_validator(user: User):
    """
    Validate that a user cannot be a player and manager of the same
    tournament
    """
    p_regs = {
        (obj.user, obj.team.tournament) for obj in Player.objects.filter(user=user)
    }
    m_regs = {
        (obj.user, obj.team.tournament) for obj in Manager.objects.filter(user=user)
    }
    s_regs = {
        (obj.user, obj.team.tournament) for obj in Substitute.objects.filter(user=user)
    }
    if len(m_regs.intersection(p_regs)) > 0 or len(s_regs.intersection(p_regs)) > 0 or len(s_regs.intersection(m_regs)) > 0:
        raise ValidationError(
            _("Utilisateur⋅rice déjà inscrit⋅e dans ce tournois (rôles distincts)")
        )

def max_players_per_team_reached(team: Team, exclude=None):
    """Validate the number of players in a team"""
    if len(team.get_players().exclude(id=exclude)) >= team.get_tournament().get_game().get_players_per_team():
        return True
    return False

def max_substitue_per_team_reached(team: Team, exclude=None):
    """Validate the number of sub in a team"""
    if len(team.get_substitutes().exclude(id=exclude)) >= team.get_tournament().get_game().get_substitute_players_per_team():
        return True
    return False

def tournament_announced(tournament: Tournament):
    """Validate if a tournament is announced"""
    if tournament.is_announced:
        return True
    return False

def tournament_registration_full(tournament: Tournament, exclude=None):
    """Validate if a tournament is full"""
    if exclude is not None:
        return False
    if tournament.get_validated_teams(exclude) >= tournament.get_max_team():
        return True
    return False