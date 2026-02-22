from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('stats/', views.stats, name='stats'),
]