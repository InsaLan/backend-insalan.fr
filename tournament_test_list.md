# This list gives the current state regarding tournament tests by files

| Path      | Checked for new tests | Documented new tests | Implemented new tests |
|---|:---:|:---:|:---:|
| tournament/serializers.py |   |   |   |
| tournament/models/caster.py | N/A | N/A | N/A |
| tournament/models/event.py |   |   |   |
| tournament/models/seat.py | N/A | N/A | N/A |
| tournament/models/substitute.py |   |   |   |
| tournament/models/swiss.py |   |   |   |
| tournament/models/game.py |   |   |   |
| tournament/models/validators.py |   |   |   |
| tournament/models/seat_slot.py | N/A | N/A | N/A |
| tournament/models/team.py |   |   |   |
| tournament/models/player.py |   |   |   |
| tournament/models/group.py |   |   |   |
| tournament/models/stage.py | N/A | N/A | N/A |
| tournament/models/name_validator.py |   |   |   |
| tournament/models/payement_status.py | N/A | N/A | N/A |
| tournament/models/bracket.py |   |   |   |
| tournament/models/tournament.py |   |   |   |
| tournament/models/manager.py |   |   |   |
| tournament/models/mailer.py |   |   |   |
| tournament/models/match.py | &check; | &check; |   |
| tournament/models/game_processor.py |   |   |   |
| tournament/apps.py | &check; | &check; |   |
| tournament/admin.py |   |   |   |
| tournament/manage/swiss.py |   |   |   |
| tournament/manage/group.py |   |   |   |
| tournament/manage/bracket.py | &check; (partial) | &check; |   |
| tournament/manage/match.py | partial (other match types) | partial |   |
| tournament/urls.py | N/A | N/A | N/A |
| tournament/views/event.py | &check; | &check; |   |
| tournament/views/substitute.py |   |   |   |
| tournament/views/swiss.py |   |   |   |
| tournament/views/game.py |   |   |   |
| tournament/views/team.py | &check; | &check; |   |
| tournament/views/player.py | &check; | &check; |   |
| tournament/views/group.py |   |   |   |
| tournament/views/permissions.py | &check; | &check; | &check; |
| tournament/views/stage.py | &check; | &check; | WIP |
| tournament/views/bracket.py | &check; | &check; |   |
| tournament/views/tournament.py | &check; (except permissions) | WIP |   |
| tournament/views/manager.py |   |   |   |
| tournament/payment.py |   |   |   |
