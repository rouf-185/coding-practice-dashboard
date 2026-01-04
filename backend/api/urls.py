from django.urls import path
from . import views

urlpatterns = [
    path('problems/practice/', views.practice_problems, name='practice_problems'),
    path('problems/add/', views.add_problem, name='add_problem'),
    path('problems/', views.problem_list, name='problem_list'),
    path('problems/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('problems/<int:pk>/done/', views.mark_as_done, name='mark_as_done'),
]

