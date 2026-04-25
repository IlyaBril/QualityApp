from rest_framework import serializers
from .models import Defects


class DefectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Defects
        fields = '__all__'