# Generated by Django 4.2 on 2025-04-17 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0008_quizquestion_subject_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizquestion',
            name='subject',
            field=models.CharField(choices=[('all', 'All Subjects'), ('math', 'Mathematics'), ('physics', 'Physics'), ('informatics', 'Informatics')], default='all', max_length=32),
        ),
    ]
