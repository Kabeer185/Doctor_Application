# Generated by Django 5.2.1 on 2025-05-21 11:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0019_alter_patientassessment_select_sub_option'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patientassessment',
            old_name='text_amswer',
            new_name='text_answer',
        ),
    ]
