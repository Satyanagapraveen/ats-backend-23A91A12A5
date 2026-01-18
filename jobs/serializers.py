from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'description',
            'status',
            'company',
            'company_name',
            'created_by',
            'created_by_username',
            'created_at'
        ]
        read_only_fields = ['id', 'company', 'created_by', 'created_at']


class JobCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    status = serializers.ChoiceField(
        choices=[('open', 'Open'), ('closed', 'Closed')],
        default='open',
        required=False
    )
