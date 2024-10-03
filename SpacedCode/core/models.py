from django.db import models

from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_prep_mode = models.BooleanField(default=False)
    company_prep_target = models.CharField(max_length=100, blank=True)
    retention_factor = models.FloatField(default=0.8)

class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    link = models.URLField()
    problem_type = models.CharField(max_length=50)
    company_tags = models.ManyToManyField('CompanyTag', blank=True)
    last_reviewed = models.DateField(null=True, blank=True)
    next_review = models.DateField(null=True, blank=True)
    interval = models.IntegerField(default=1)
    stability = models.FloatField(default=2.5)
    difficulty = models.FloatField(default=5.0)
    retention_factor = models.FloatField(default=0.8)
    current_retention_rate = models.FloatField(null=True, blank=True)
    feynman = models.TextField(blank=True)
    average_time = models.FloatField(null=True, blank=True)

class ReviewSession(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField()
    time_taken = models.FloatField()
    explanation = models.TextField(blank=True)

class CompanyTag(models.Model):
    name = models.CharField(max_length=100)