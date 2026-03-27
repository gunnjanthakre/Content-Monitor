from rest_framework import serializers
from .models import Flag


class FlagSerializer(serializers.ModelSerializer):
    keyword_name = serializers.CharField(source='keyword.name', read_only=True)
    content_title = serializers.CharField(source='content_item.title', read_only=True)
    content_source = serializers.CharField(source='content_item.source', read_only=True)

    class Meta:
        model = Flag
        fields = [
            'id', 'keyword', 'keyword_name', 'content_item', 'content_title',
            'content_source', 'score', 'status', 'suppressed_at_content_version',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'keyword', 'keyword_name', 'content_item', 'content_title',
            'content_source', 'score', 'suppressed_at_content_version',
            'created_at', 'updated_at',
        ]


class FlagStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ['status']

    def validate_status(self, value):
        allowed = [c[0] for c in Flag.Status.choices]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(allowed)}"
            )
        return value

    def update(self, instance: Flag, validated_data: dict) -> Flag:
        new_status = validated_data['status']
        if new_status == Flag.Status.IRRELEVANT:
            instance.mark_irrelevant(instance.content_item.last_updated)
        else:
            instance.status = new_status
            instance.suppressed_at_content_version = None
            instance.save(update_fields=['status', 'suppressed_at_content_version', 'updated_at'])
        return instance