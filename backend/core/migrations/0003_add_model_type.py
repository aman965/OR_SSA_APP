# Generated by Django 5.2.1 on 2025-05-27 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_snapshot_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="scenario",
            name="model_type",
            field=models.CharField(
                choices=[
                    ("vrp", "Vehicle Routing Problem"),
                    ("inventory", "Inventory Optimization"),
                    ("scheduling", "Scheduling"),
                    ("network_flow", "Network Flow"),
                ],
                default="vrp",
                max_length=50,
            ),
        ),
    ]
