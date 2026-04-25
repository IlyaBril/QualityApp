from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)

from django_tables2 import SingleTableView

from .tables import DefectsTable
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Defects
from .serializers import DefectsSerializer
from rest_framework.response import Response
from rest_framework import status


class DefectsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            print("=" * 50)
            print("Headers:", request.headers)
            print("Auth header:", request.headers.get('Authorization'))
            print("User:", request.user)
            print("Is authenticated:", request.user.is_authenticated)
            # Получаем все дефекты
            defects = Defects.objects.all()

            # Сериализуем данные
            serializer = DefectsSerializer(defects, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

