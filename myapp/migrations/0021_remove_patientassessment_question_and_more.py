# Generated by Django 5.2.1 on 2025-05-21 13:24

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0020_rename_text_amswer_patientassessment_text_answer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientassessment',
            name='question',
        ),
        migrations.RemoveField(
            model_name='patientassessment',
            name='select_main_option',
        ),
        migrations.RemoveField(
            model_name='patientassessment',
            name='select_sub_option',
        ),
        migrations.RemoveField(
            model_name='patientassessment',
            name='text_answer',
        ),
        migrations.AddField(
            model_name='patientassessment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='patientassessment',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patientassessment', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='PatientAssessmentAns',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_answer', models.TextField(blank=True, null=True)),
                ('assessment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Answer', to='myapp.patientassessment')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assessment_question', to='myapp.question')),
                ('select_main_option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assessment_main_option', to='myapp.option')),
                ('select_sub_option', models.ManyToManyField(related_name='assessment_sub_option', to='myapp.option')),
            ],
        ),
    ]
