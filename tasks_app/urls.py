from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('stats/', views.stats, name='stats'),
    path('stats/export/', views.export_stats_csv, name='export_stats_csv'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.user_management, name='user_management'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]