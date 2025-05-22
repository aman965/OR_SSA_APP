from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Upload, Snapshot, Scenario
from .serializers import UploadSerializer, SnapshotSerializer, ScenarioSerializer
from repositories.scenario_repo import ScenarioRepo

# Create your views here.

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer

class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer

    @action(detail=True, methods=['post'])
    def add_constraint(self, request, pk=None):
        """Add a constraint prompt to the scenario."""
        prompt = request.data.get('prompt')
        if not prompt:
            return Response(
                {'error': 'prompt is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ScenarioRepo.add_constraint_prompt(pk, prompt)
            scenario = ScenarioRepo.get(pk)
            return Response(ScenarioSerializer(scenario).data)
        except Scenario.DoesNotExist:
            return Response(
                {'error': 'Scenario not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
