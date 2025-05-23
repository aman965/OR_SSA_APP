from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import SnapshotSummary

router = DefaultRouter()
router.register(r'uploads', views.UploadViewSet)
router.register(r'snapshots', views.SnapshotViewSet)
router.register(r'scenarios', views.ScenarioViewSet)
router.register(r'datasets', views.DatasetViewSet)

urlpatterns = [
    path('snapshots/summary/', SnapshotSummary.as_view(), name='snapshot-summary'),
    path('', include(router.urls)),
] 