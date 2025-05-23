from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Upload, Snapshot, Scenario, Dataset
from .serializers import UploadSerializer, SnapshotSerializer, ScenarioSerializer, SnapshotSummarySerializer, DatasetSerializer
from repositories.scenario_repo import ScenarioRepo

# Create your views here.

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print('SNAPSHOT CREATE ERROR:', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

class SnapshotSummary(APIView):
    # permission_classes = [IsAuthenticated]  # Temporarily removed for debugging

    def get(self, request):
        qs = (Snapshot.objects
              .only("id", "name", "created_at", "solution_status", "owner_id")
              .select_related("owner")
              .order_by("-created_at"))
        ser = SnapshotSummarySerializer(qs, many=True)
        return Response(ser.data)

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
