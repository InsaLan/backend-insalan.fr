from django.shortcuts import render

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
# view that return 418 status code
class CoffeeView(APIView):
    def get(self, request, format=None):
        return Response(status=status.HTTP_418_IM_A_TEAPOT)