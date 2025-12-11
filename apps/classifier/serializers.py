"""
분류 API Serializers
"""
from rest_framework import serializers


class ClassifyRequestSerializer(serializers.Serializer):
    """메일 분류 요청"""
    mail_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=20,
        help_text='분류할 메일 ID 목록 (최대 20개)'
    )


class ClassificationStartResponseSerializer(serializers.Serializer):
    """분류 시작 응답"""
    classification_id = serializers.CharField()
    mail_count = serializers.IntegerField()
    started_at = serializers.DateTimeField()


class FolderResultSerializer(serializers.Serializer):
    """폴더 결과"""
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    path = serializers.CharField()


class ClassificationResultItemSerializer(serializers.Serializer):
    """개별 분류 결과"""
    mail_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['success', 'failed'])
    folder = FolderResultSerializer(allow_null=True)
    is_new_folder = serializers.BooleanField(default=False)
    confidence = serializers.FloatField(default=0.0)
    error = serializers.CharField(allow_null=True, required=False)


class ClassificationSummarySerializer(serializers.Serializer):
    """분류 요약"""
    total = serializers.IntegerField()
    success = serializers.IntegerField()
    failed = serializers.IntegerField()
    new_folders_created = serializers.IntegerField()


class ClassificationStatusResponseSerializer(serializers.Serializer):
    """분류 상태 응답"""
    classification_id = serializers.CharField()
    state = serializers.ChoiceField(choices=['pending', 'in_progress', 'completed', 'failed'])
    results = ClassificationResultItemSerializer(many=True)
    summary = ClassificationSummarySerializer()
    started_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    error = serializers.CharField(allow_null=True, required=False)
