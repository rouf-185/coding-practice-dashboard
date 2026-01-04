from rest_framework import serializers
from .models import Problem


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'title', 'leetcode_url', 'difficulty', 'solved_date', 'created_at', 'last_practiced']
        read_only_fields = ['id', 'created_at']


class ProblemListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(read_only=True)
    
    class Meta:
        model = Problem
        fields = ['id', 'title', 'leetcode_url', 'difficulty', 'solved_date', 'last_practiced', 'category']


class AddProblemSerializer(serializers.Serializer):
    leetcode_url = serializers.URLField()

