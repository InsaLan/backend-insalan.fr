from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tournament import serializers

from ..models import Game
from .permissions import ReadOnly

class GameList(generics.ListCreateAPIView):
    """List all known games"""

    pagination_class = None
    queryset = Game.objects.all().order_by("id")
    serializer_class = serializers.GameSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
        responses={
            201: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à créer un match")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Create a game"""
        return super().post(request, *args, **kwargs)


class GameDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a game"""

    serializer_class = serializers.GameSerializer
    queryset = Game.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier ce match")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Jeu non trouvé")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """Update a game"""
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Jeu supprimé")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer ce jeu")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Jeu non trouvé")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """Delete a game"""
        return super().delete(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "team1_score": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("Score de l'équipe 1")
                ),
                "team2_score": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("Score de l'équipe 2")
                ),
            },
        ),
        responses={
            200: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "team1_score": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Score de l'équipe 1")
                    ),
                    "team2_score": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Score de l'équipe 2")
                    ),
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier ce match")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Match introuvable")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update a game
        """
        return super().patch(request, *args, **kwargs)
