from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    processing_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'user', 'status', 'created_at', 'started_at', 
                           'completed_at', 'progress', 'error_message', 
                           'retry_count', 'output_data', 'output_file']
    
    def get_processing_time(self, obj):
        return obj.processing_time
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'status', 'progress', 'error_message', 'processing_time']