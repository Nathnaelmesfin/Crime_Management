# Generated by Django 5.0.6 on 2025-06-26 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crime', '0005_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='status',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
