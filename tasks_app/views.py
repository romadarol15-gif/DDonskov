from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, User
from .forms import TaskForm, UserProfileForm, UserCreateForm
from django.db.models import Count, Q
import json

@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    equip_filter = request.GET.get('equipment', '')

    if request.user.role == 'employee':
        tasks = Task.objects.filter(assignee=request.user)
    else:
        tasks = Task.objects.all()

    if query:
        tasks = tasks.filter(Q(number__icontains=query) | Q(title__icontains=query) | Q(contact_info__icontains=query))
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    else:
        # По умолчанию скрываем закрытые для удобства на главной
        if request.user.role == 'employee' and not query:
            tasks = tasks.exclude(status='closed')
        elif not query:
            tasks = tasks.filter(Q(status='new') | Q(assignee__isnull=True))

    if equip_filter:
        tasks = tasks.filter(equipment_type=equip_filter)

    tasks = tasks.order_order_by('-created_at') if hasattr(tasks, 'order_by') else tasks.order_by('-id')

    context = {
        'tasks': tasks,
        'statuses': Task.STATUS_CHOICES,
        'equipments': Task.EQUIPMENT_CHOICES,
        'q': query,
        'current_status': status_filter,
        'current_equip': equip_filter
    }
    return render(request, 'tasks_app/dashboard.html', context)

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks_app/task_detail.html', {'form': form, 'task': task})

@login_required
def task_create(request):
    if request.user.role not in ['superuser', 'director']:
        messages.error(request, 'У вас нет прав для создания задач.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            import uuid
            task = form.save(commit=False)
            if not task.number:
                task.number = f"TSK-NEW-{uuid.uuid4().hex[:6].upper()}"
            task.save()
            messages.success(request, 'Новая задача успешно создана.')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'tasks_app/task_form.html', {'form': form, 'title': 'Создание новой задачи'})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'tasks_app/profile.html', {'form': form})

@login_required
def user_management(request):
    if request.user.role not in ['superuser', 'director']:
        messages.error(request, 'У вас нет прав для управления пользователями.')
        return redirect('dashboard')
        
    users = User.objects.all().order_by('username')
    return render(request, 'tasks_app/user_management.html', {'users': users})

@login_required
def user_create(request):
    if request.user.role not in ['superuser', 'director']:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'Пользователь {user.username} успешно создан.')
            return redirect('user_management')
    else:
        form = UserCreateForm()
    return render(request, 'tasks_app/user_form.html', {'form': form, 'title': 'Создание пользователя'})

@login_required
def user_delete(request, pk):
    if request.user.role not in ['superuser', 'director']:
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser and request.user.pk != user.pk:
         messages.error(request, 'Нельзя удалить другого суперпользователя.')
    else:
         user.delete()
         messages.success(request, 'Пользователь удален.')
    return redirect('user_management')

@login_required
def stats(request):
    if request.user.role == 'employee':
        # Статистика только по своим задачам
        status_counts = list(Task.objects.filter(assignee=request.user).values('status').annotate(count=Count('id')))
        equip_counts = list(Task.objects.filter(assignee=request.user).values('equipment_type').annotate(count=Count('id')))
        context = {
            'status_counts': json.dumps(status_counts),
            'equip_counts': json.dumps(equip_counts),
            'is_employee': True
        }
        return render(request, 'tasks_app/stats.html', context)
        
    if request.user.role not in ['superuser', 'director', 'manager']:
        return redirect('dashboard')
    
    # Общая статистика для руководителей
    status_counts = list(Task.objects.values('status').annotate(count=Count('id')))
    equip_counts = list(Task.objects.values('equipment_type').annotate(count=Count('id')))
    employee_stats = User.objects.filter(role='employee').annotate(task_count=Count('tasks'))

    context = {
        'status_counts': json.dumps(status_counts),
        'equip_counts': json.dumps(equip_counts),
        'employee_stats': employee_stats,
        'is_employee': False
    }
    return render(request, 'tasks_app/stats.html', context)