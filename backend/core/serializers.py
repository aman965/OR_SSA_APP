from rest_framework import serializers
from .models import Upload, Snapshot, Scenario

class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['id', 'name', 'file', 'uploaded_at']

class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ['id', 'name', 'linked_upload', 'created_at']

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = [
            'id', 'name', 'snapshot', 
            'param1', 'param2', 'param3', 'param4', 'param5',
            'gpt_prompt', 'gpt_response', 'status', 'reason',
            'created_at'
        ] 