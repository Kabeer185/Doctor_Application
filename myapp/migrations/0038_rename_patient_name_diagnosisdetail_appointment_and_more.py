# Generated by Django 5.2.1 on 2025-06-11 16:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0037_rename_patient_diagnosisdetail_patient_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='diagnosisdetail',
            old_name='patient_name',
            new_name='appointment',
        ),
        migrations.RenameField(
            model_name='labreport',
            old_name='patient_name',
            new_name='appointment',
        ),
    ]
