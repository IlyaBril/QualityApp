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
            defects = Defects.objects.all()
            serializer = DefectsSerializer(defects, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
