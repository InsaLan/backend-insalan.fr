"""
Command handler to populate the database with dummy data

Authors:
 - Amelia "Lymkwi" González, 2023
 """

import io
import os

from random import randint, choice

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

# Our models
import insalan.settings
from insalan.tournament.models import (
    Event,
    Game,
    Tournament,
    Team,
    Player,
    Manager,
    Substitute,
    PaymentStatus,
)
from insalan.user.models import User
from insalan.partner.models import Partner


def generate_garbage(count=32):
    """Generate a desired length of garbage"""
    return ("".join([hex(x)[2:] for x in os.urandom(count // 2)]))[:count]


def pull_id(collection):
    """Pull an identifier, if any, at random, from a collection. None if empty."""
    if len(collection) == 0:
        return None
    ret = choice(collection)
    collection.remove(ret)
    return ret


def payment_random():
    """Pull a payment status at random with a skewed distribution"""
    roll = randint(0, 100)
    if roll < 15:
        return PaymentStatus.PAY_LATER
    if roll < 75:
        return PaymentStatus.PAID
    return PaymentStatus.NOT_PAID


class Command(BaseCommand):
    """The `populate` command handler class"""

    help = "Populate the database with dummy data for testing purposes"

    def add_arguments(self, parser):
        """Add declarations for the arguments this command will take"""
        # If people keep telling you "hey, this is production"
        # Tell them: "NO, THIS IS PATRICK"
        parser.add_argument(
            "--no-this-is-patrick",
            action="store_true",
            help="Force the prompt that comes up if you're in production",
        )

        parser.add_argument(
            "--yes-please",
            action="store_true",
            help="Force the prompt that asks if you're really sure",
        )

    def generate_partner(self):
        """Generate a partner"""
        par = Partner.objects.create(
            name="partner_" + generate_garbage(randint(50, 150)),
            url="https://example.com/" + generate_garbage(randint(10, 20)),
            logo=self.generate_logo(),
            partner_type=choice(
                [Partner.PartnerType.PARTNER, Partner.PartnerType.SPONSOR]
            ),
        )
        print(
            "P" if par.partner_type == Partner.PartnerType.PARTNER else "S",
            end="",
            flush=True,
        )

    def generate_logo(self):
        """Generate an uploaded logo file"""
        test_img = io.BytesIO(generate_garbage(randint(500, 1000)).encode("utf-8"))
        test_img.name = (
            generate_garbage(randint(5, 20))
            + "."
            + choice(["png", "jpg", "jpeg", "svg", "webp", "avif"])
        )
        return SimpleUploadedFile(test_img.name, test_img.getvalue())

    def generate_events(self):
        """Generate the events, returning a list of Event objects"""
        print("-" * 40)
        print("Events:")
        events = []
        for _ in range(randint(5, 8)):
            events.append(
                Event.objects.create(
                    name=f"Insalan {generate_garbage(randint(15, 30))}",
                    description=generate_garbage(randint(2, 127)),
                    year=randint(2003, 2024),
                    month=randint(1, 13),
                    ongoing=randint(0, 100) < 50,
                    logo=self.generate_logo(),
                )
            )
            print(events[-1])

        # If none are ongoing
        event_ids = Event.get_ongoing_ids()
        if len(event_ids) == 0:
            # Designate one
            choice(events).ongoing = True

        print("Ongoing:", ",".join(map(str, Event.get_ongoing_ids())))

        return events

    def generate_tournaments(self, events, games):
        """Generate tournaments"""
        print("-" * 40)
        print("Tournament:")
        for event in events:
            game_ids_free = [game.id for game in games]

            for _ in range(randint(3, 5)):
                if len(game_ids_free) == 0:
                    break
                game_id = choice(game_ids_free)
                game_ids_free.remove(game_id)

                tourney = Tournament.objects.create(
                    event=event,
                    game=Game.objects.get(id=game_id),
                    name="tourney_" + generate_garbage(randint(18, 26)),
                    rules=generate_garbage(randint(40000, 45000)),
                    maxTeam=randint(1, 10),
                    logo=self.generate_logo(),
                    is_announced=randint(0, 100) < 50,
                    player_price_online=randint(0, 50),
                    player_price_onsite=randint(0, 50),
                    manager_price_online=randint(0, 50),
                    manager_price_onsite=randint(0, 50),
                    substitute_price_online=randint(0, 50),
                    substitute_price_onsite=randint(0, 50),
                )
                print(tourney)

    def generate_singleplayer_team(self, pool_of_users, tourney):
        """Generate a singleplayer team"""
        user_id = pull_id(pool_of_users)
        if user_id is None:
            return
        user = User.objects.get(id=user_id)
        team = Team.objects.create(tournament=tourney, name="sp_" + user.username[5:17])
        Player.objects.create(
            team=team,
            user=user,
            payment_status=payment_random(),
            name_in_game=generate_garbage(randint(5, 15)),
        )
        print(f"\r    [{team}] \u2713", end="\r")

    def generate_games(self):
        """Generate games, returning a list of Game objects"""
        print("-" * 40)
        print("Games:")
        games = []
        for _ in range(randint(2, 8)):
            games.append(
                Game.objects.create(
                    name=f"Game {randint(0, 127)}",
                    short_name=f"G{randint(0, 99)}",
                    players_per_team=randint(1, 10),
                )
            )
            print(games[-1])
        return games

    def generate_multiplayer_team(self, pool_of_users, tourney):
        """Generate a team of multiple players and potentially a manager"""
        team = Team.objects.create(
            tournament=tourney,
            name="team_" + generate_garbage(randint(25, 32)),
        )

        # each team will have an okay amount of people around 8
        for _ in range(randint(8, 10)):
            # Register a player
            user_id = pull_id(pool_of_users)
            if user_id is None:
                break
            Player.objects.create(
                user=User.objects.get(id=user_id),
                team=team,
                payment_status=payment_random(),
                name_in_game=generate_garbage(randint(5, 15)),
            )
            print(".", end="", flush=True)

        for _ in range(choice([0, 1, 1, 2])):
            # Regiter a manager
            user_id = pull_id(pool_of_users)
            if user_id is None:
                break
            Manager.objects.create(
                user=User.objects.get(id=user_id),
                team=team,
                payment_status=payment_random(),
            )
            print(".", end="", flush=True)

        for _ in range(choice([0, 1, 1, 2])):
            # Regiter a substitute
            user_id = pull_id(pool_of_users)
            if user_id is None:
                break
            Substitute.objects.create(
                user=User.objects.get(id=user_id),
                team=team,
                payment_status=payment_random(),
                name_in_game=generate_garbage(randint(5, 15)),
            )
            print(".", end="", flush=True)
        print(f"\r    [{team}] \u2713    ")

    def handle(self, *_, **options):
        """Command handler"""

        # If we are in debug, and this isn't Patrick
        if not insalan.settings.DEBUG and not options.get("no_this_is_patrick", False):
            raise CommandError(
                """
                WARNING!! YOU ARE TRYING TO INJECT DUMMY DATA INTO AN APP THAT
                IS RUNNING IN PRODUCTION MODE. PLEASE EXPORT `DEV` AS `1` OR
                FORCE THIS PROMPT TO SILENCE!
                """
            )

        if not options.get("yes_please", False):
            print(
                """
                Warning! You're about to inject dummy data!
                If you do not want to do that, press the SIGINT key sequence,
                which, by default, should be Control+C or Command+C.

                Or press Enter to continue.
                """
            )
            input()

        # Alright, let's do this
        self.populate_dummy_data()

    def populate_dummy_data(self):
        """Actually populate the database"""

        # Let's create some events
        events = self.generate_events()
        # And games
        games = self.generate_games()
        # Add tournaments
        self.generate_tournaments(events, games)

        # Generate a random pool of |events| * ~80
        print("-" * 40)
        print("Users:")
        users = []
        for _ in range(len(events) * randint(75, 85)):
            users.append(
                User.objects.create(
                    username="user_" + generate_garbage(40),
                    is_staff=False,
                    is_superuser=False,
                    first_name="Jane",
                    last_name="Doe",
                    email=f"{generate_garbage(60)}@example.net",
                )
            )
            print(users[-1], end="    \r")

        print(" " * 60 + "\r" + f"Generated {len(users)} users")

        print("-" * 40)
        print("Registrations:")
        # Now, register them
        for event in events:
            print(f"{event}:")
            pool_of_users = [user.id for user in users]
            for tourney in event.get_tournaments():
                print(f"  [{tourney}]::")
                is_singleplayer = randint(0, 100) < 25
                if is_singleplayer:
                    # Create like 15 to 20 singleplayer teams
                    for _ in range(randint(15, 20)):
                        self.generate_singleplayer_team(pool_of_users, tourney)
                    print("")
                else:
                    # Create, like, idk, 5 to 6 teams?
                    for _ in range(randint(5, 6)):
                        self.generate_multiplayer_team(pool_of_users, tourney)

        print("-" * 40)
        print("Partners & Sponsors:")
        for _ in range(randint(10, 20)):
            self.generate_partner()

        print("\nDone")
