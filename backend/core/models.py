from django.db import models
from django.conf import settings
from datetime import datetime  # noqa: TCH003

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class Dataset(models.Model):
    """A data file uploaded by a user, formerly *UploadedDataset* in SQLAlchemy."""

    name: str = models.CharField(max_length=255, unique=True)
    file_path: str = models.CharField(max_length=1024)
    file_type: str = models.CharField(max_length=50)

    owner: "settings.AUTH_USER_MODEL" = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="datasets",
        null=True,
        blank=True,
    )

    created_at: "datetime" = models.DateTimeField(auto_now_add=True)
    updated_at: "datetime" = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # noqa: D401
        return self.name

# ---------------------------------------------------------------------------
# Upload (legacy)
# ---------------------------------------------------------------------------

class Upload(models.Model):
    name = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

class Snapshot(models.Model):
    name = models.CharField(max_length=255, unique=True)
    dataset: Dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="snapshots")  # type: ignore[valid-type]
    description = models.TextField(blank=True, null=True)

    owner: "settings.AUTH_USER_MODEL" = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="snapshots",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

class Scenario(models.Model):
    name = models.CharField(max_length=255)
    snapshot: Snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name="scenarios")  # type: ignore[valid-type]
    param1 = models.FloatField()
    param2 = models.IntegerField()
    param3 = models.IntegerField()
    param4 = models.BooleanField()
    param5 = models.BooleanField()
    gpt_prompt = models.TextField(blank=True, null=True)
    gpt_response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    reason = models.TextField(blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True, null=True)

    owner: "settings.AUTH_USER_MODEL" = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scenarios",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.snapshot.name} - {self.name}"

# ---------------------------------------------------------------------------
# Solution
# ---------------------------------------------------------------------------

class Solution(models.Model):
    """Stores solver results for a scenario."""

    scenario: Scenario = models.OneToOneField(  # type: ignore[valid-type]
        Scenario,
        on_delete=models.CASCADE,
        related_name="solution",
    )

    summary: dict[str, object] | None = models.JSONField(blank=True, null=True)

    owner: "settings.AUTH_USER_MODEL" = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solutions",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # noqa: D401
        return f"Solution for {self.scenario.name}"
