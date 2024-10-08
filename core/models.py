from django.db import models

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_prep_mode = models.BooleanField(default=False)
    company_prep_target = models.CharField(max_length=100, blank=True)
    retention_factor = models.FloatField(default=0.8)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

DIFFICULTY_ORDER = {
    "Arrays": 1,
    "Hashing": 2,
    "2P": 3,
    "Stack": 4,
    "Sorting": 5,
    "Binary Search": 6,
    "Sliding Window": 7,
    "Linked List": 8,
    "Greedy": 9,
    "Heap": 10,
    "Intervals": 11,
    "Trees": 12,
    "Math": 13,
    "Graphs": 14,
    "Backtracking": 15,
    "Tries": 16,
    "DP": 17
}


PROBLEM_TYPE_CHOICES = sorted(
    [(key, key) for key in DIFFICULTY_ORDER.keys()],
    key=lambda x: DIFFICULTY_ORDER[x[0]]
)

class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=100)
    link = models.URLField(blank=True, null=True)
    problem_type = models.CharField(max_length=50, choices=PROBLEM_TYPE_CHOICES)
    company_tags = models.ManyToManyField('CompanyTag', related_name='questions')
    last_reviewed = models.DateField(auto_now=True)
    next_review = models.DateField()
    interval = models.IntegerField(default=1)
    stability = models.FloatField(default=0.5)
    difficulty = models.FloatField(default=5)
    retention_factor = models.FloatField(default=0.8)
    current_retention_rate = models.FloatField(default=0.5)
    feynman = models.TextField(blank=True, null=True)
    average_time = models.FloatField(default=0.0)
    ratings = models.JSONField(default=list, blank=True)
    solving_time = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.text[:50]


class ReviewSession(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField()
    time_taken = models.FloatField()
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Review of {self.question} by {self.user} on {self.date}"

class CompanyTag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name