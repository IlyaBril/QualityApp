from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Defects
from .serializers import DefectsSerializer
from authentication.permissions import DepartmentPermission
from rest_framework.response import Response
from rest_framework import status


class DefectsListView(APIView):
    permission_classes = [IsAuthenticated, DepartmentPermission]

    def get(self, request):
        try:
            if request.user.is_superuser or request.user.is_staff:
                defects = Defects.objects.all()
            else:
                defects = Defects.objects.filter(responsible_department=self.request.user.profile.department)

            serializer = DefectsSerializer(defects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
