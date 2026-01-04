from django.db import models
from django.contrib.auth.models import User


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problems')
    title = models.CharField(max_length=255)
    leetcode_url = models.URLField(max_length=500)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    solved_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_practiced = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-solved_date']

    def __str__(self):
        return f"{self.title} ({self.difficulty})"
