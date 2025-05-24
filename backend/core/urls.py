from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadViewSet, SnapshotViewSet, ScenarioViewSet
from . import vrp_views  # NEW VRP views

router = DefaultRouter()
router.register(r'uploads', UploadViewSet)
router.register(r'snapshots', SnapshotViewSet)
router.register(r'scenarios', ScenarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 