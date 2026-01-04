from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.utils import timezone
from datetime import timedelta
from .models import Problem
from .serializers import ProblemSerializer, ProblemListSerializer, AddProblemSerializer
from .utils import scrape_leetcode_problem


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def practice_problems(request):
    """
    Get problems to practice today based on spaced repetition:
    - Problems solved 2 days ago
    - Problems solved 5 days ago
    - Problems solved 10 days ago
    - If weekend: 2 random additional problems
    """
    today = timezone.now().date()
    problems = []
    problem_ids = set()  # To avoid duplicates
    
    # Problems solved 2, 5, 10 days ago
    for days_ago in [2, 5, 10]:
        target_date = today - timedelta(days=days_ago)
        date_problems = Problem.objects.filter(
            user=request.user,
            solved_date__date=target_date
        )
        
        for problem in date_problems:
            if problem.id not in problem_ids:
                problem_ids.add(problem.id)
                problem_data = ProblemListSerializer(problem).data
                problem_data['category'] = f'Solved {days_ago} days ago'
                problems.append(problem_data)
    
    # Weekend random problems (Saturday=5, Sunday=6)
    if today.weekday() in [5, 6]:
        random_problems = Problem.objects.filter(
            user=request.user
        ).exclude(id__in=problem_ids).order_by('?')[:2]
        
        for problem in random_problems:
            problem_ids.add(problem.id)
            problem_data = ProblemListSerializer(problem).data
            problem_data['category'] = 'Random Practice'
            problems.append(problem_data)
    
    return Response(problems, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_problem(request):
    """
    Add a new problem by scraping Leetcode URL.
    """
    serializer = AddProblemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    leetcode_url = serializer.validated_data['leetcode_url']
    
    # Scrape problem details
    problem_data = scrape_leetcode_problem(leetcode_url)
    
    if not problem_data:
        return Response(
            {'error': 'Failed to scrape problem details. Please check the URL.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create problem
    problem = Problem.objects.create(
        user=request.user,
        title=problem_data['title'],
        leetcode_url=leetcode_url,
        difficulty=problem_data['difficulty'],
        solved_date=timezone.now()
    )
    
    serializer = ProblemSerializer(problem)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def problem_list(request):
    """
    Get all problems for the authenticated user.
    """
    problems = Problem.objects.filter(user=request.user)
    serializer = ProblemSerializer(problems, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def problem_detail(request, pk):
    """
    Retrieve, update or delete a problem.
    """
    try:
        problem = Problem.objects.get(pk=pk, user=request.user)
    except Problem.DoesNotExist:
        return Response(
            {'error': 'Problem not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = ProblemSerializer(problem)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProblemSerializer(problem, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        problem.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_done(request, pk):
    """
    Mark a problem as practiced by updating last_practiced timestamp.
    """
    try:
        problem = Problem.objects.get(pk=pk, user=request.user)
    except Problem.DoesNotExist:
        return Response(
            {'error': 'Problem not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    problem.last_practiced = timezone.now()
    problem.save()
    
    serializer = ProblemSerializer(problem)
    return Response(serializer.data, status=status.HTTP_200_OK)
