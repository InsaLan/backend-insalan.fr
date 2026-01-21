from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_yasg.utils import swagger_auto_schema  # type: ignore[import]
from drf_yasg import openapi  # type: ignore[import]

from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from insalan.tournament import serializers

from ..models import Game
from ..models.game_processor import (
    get_processor_default_parameters,
    get_processor_parameters_schema,
)
from .permissions import ReadOnly

class GameList(generics.ListCreateAPIView[Game]):  # pylint: disable=unsubscriptable-object
    """List all known games"""

    pagination_class = None
    queryset = Game.objects.all().order_by("id")
    serializer_class = serializers.GameSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a game"""
        return super().post(request, *args, **kwargs)


# pylint: disable-next=unsubscriptable-object
class GameDetails(generics.RetrieveUpdateDestroyAPIView[Game]):
    """Details about a game"""

    serializer_class = serializers.GameSerializer
    queryset = Game.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a game"""
        return super().put(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a game"""
        return super().delete(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a game
        """
        return super().patch(request, *args, **kwargs)


class GameProcessorParameters(generics.GenericAPIView[Game]):  # pylint: disable=unsubscriptable-object
    """Get the default parameters and schema for a game processor"""

    permission_classes = [permissions.IsAdminUser | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        manual_parameters=[
            openapi.Parameter(
                "processor",
                openapi.IN_QUERY,
                description=_("Le nom court du processeur de jeu (ex: 'LoL', 'None')"),
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "default_parameters": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description=_("Paramètres par défaut pour ce processeur")
                    ),
                    "parameters_schema": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description=_("Schéma des paramètres disponibles")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Paramètre 'processor' manquant")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Processeur non trouvé")
                    )
                }
            )
        }
    )
    def get(self, request: Request) -> Response:
        """
        Get default parameters and schema for a game processor
        """
        processor_name = request.query_params.get("processor")
        
        if not processor_name:
            return Response(
                {"err": _("Le paramètre 'processor' est requis")},
                status=400
            )
        
        default_params = get_processor_default_parameters(processor_name)
        schema = get_processor_parameters_schema(processor_name)
        
        if not default_params and not schema:
            return Response(
                {"err": _("Processeur non trouvé ou sans paramètres")},
                status=404
            )
        
        return Response({
            "default_parameters": default_params,
            "parameters_schema": schema
        })
