from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'uploads', views.UploadViewSet)
router.register(r'snapshots', views.SnapshotViewSet)
router.register(r'scenarios', views.ScenarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 