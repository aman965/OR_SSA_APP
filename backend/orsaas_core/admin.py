from django.contrib import admin
from .models import Upload, Snapshot, Scenario

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at')
    search_fields = ('name',)

@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ('name', 'linked_upload', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'snapshot', 'status', 'created_at')
    search_fields = ('name',)
    list_filter = ('status', 'created_at')
