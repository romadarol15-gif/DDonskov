from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Task, User
from .forms import TaskForm
from django.db.models import Count
import json

@login_required
def dashboard(request):
    if request.user.role == 'employee':
        tasks = Task.objects.filter(assignee=request.user).exclude(status='closed')
    else:
        tasks = Task.objects.filter(status='new') | Task.objects.filter(assignee__isnull=True)
    return render(request, 'tasks_app/dashboard.html', {'tasks': tasks})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks_app/task_detail.html', {'form': form, 'task': task})

@login_required
def stats(request):
    if request.user.role not in ['superuser', 'director', 'manager']:
        return redirect('dashboard')
    
    status_counts = list(Task.objects.values('status').annotate(count=Count('id')))
    equip_counts = list(Task.objects.values('equipment_type').annotate(count=Count('id')))
    employee_stats = User.objects.filter(role='employee').annotate(task_count=Count('tasks'))

    context = {
        'status_counts': json.dumps(status_counts),
        'equip_counts': json.dumps(equip_counts),
        'employee_stats': employee_stats
    }
    return render(request, 'tasks_app/stats.html', context)