from django.db import models

# Create your models here.

class Upload(models.Model):
    name = models.CharField(max_length=100, unique=True)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Snapshot(models.Model):
    name = models.CharField(max_length=100, unique=True)
    linked_upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Scenario(models.Model):
    name = models.CharField(max_length=100)
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    param1 = models.FloatField(default=1.0)
    param2 = models.IntegerField(default=0)
    param3 = models.IntegerField(default=50)
    param4 = models.BooleanField(default=False)
    param5 = models.BooleanField(default=False)
    gpt_prompt = models.TextField(blank=True)
    gpt_response = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='created')  # created, solving, solved, failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
