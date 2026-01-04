from django.contrib import admin
from .models import Problem


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'user', 'solved_date', 'last_practiced']
    list_filter = ['difficulty', 'solved_date']
    search_fields = ['title', 'leetcode_url']
    readonly_fields = ['created_at']
