from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.db.models.signals import post_save
from django.dispatch import receiver

class PromptData(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.TextField(blank=True)
    output = models.TextField(blank=True)
    img = models.TextField(blank=True)

    def __str__(self):
        return self.output


SUBJECT_CHOICES = [
    ('all', 'All Subjects'),
    ('math', 'Mathematics'),
    ('physics', 'Physics'),
    ('informatics', 'Informatics'),
]


class QuizQuestion(models.Model):
    subject = models.CharField(max_length=32, choices=SUBJECT_CHOICES, default='all')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.question

class Grade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.percentage}%"

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     avatar = models.ImageField(
#         upload_to='avatars/',
#         default='avatars/default.png',
#         blank=True
#     )

#     def __str__(self):
#         return f"{self.user.username} Profile"

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#     instance.profile.save()
