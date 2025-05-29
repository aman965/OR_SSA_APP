from django.db import models

# Create your models here.

class Upload(models.Model):
    name = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Snapshot(models.Model):
    name = models.CharField(max_length=255, unique=True)
    linked_upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    model_type = models.CharField(
        max_length=20,
        choices=[('vrp', 'VRP'), ('inventory', 'Inventory')],
        default='vrp'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Scenario(models.Model):
    MODEL_TYPE_CHOICES = [
        ('vrp', 'Vehicle Routing Problem'),
        ('inventory', 'Inventory Optimization'),
        ('scheduling', 'Scheduling'),
        ('network_flow', 'Network Flow'),
    ]
    
    name = models.CharField(max_length=255)
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES, default='vrp')
    param1 = models.FloatField()
    param2 = models.IntegerField()
    param3 = models.IntegerField()
    param4 = models.BooleanField()
    param5 = models.BooleanField()
    gpt_prompt = models.TextField(blank=True, null=True)
    gpt_response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.snapshot.name} - {self.name}"
