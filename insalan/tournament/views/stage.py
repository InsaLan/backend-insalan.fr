from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAdminUser

from ..models import Stage
from ..serializers import StageSerializer

# pylint: disable-next=unsubscriptable-object
class CreateUpdateDeleteStage(CreateAPIView[Stage], UpdateAPIView[Stage], DestroyAPIView[Stage]):
    """Create new tournament stage"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    permission_classes = [IsAdminUser]
