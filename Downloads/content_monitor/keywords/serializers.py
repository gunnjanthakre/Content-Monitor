from rest_framework import serializers
from .models import Keyword


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']