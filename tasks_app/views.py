from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Task, User, TaskComment, TaskLog
from .forms import TaskForm, UserProfileForm, UserCreateForm, UserEditForm
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import timedelta
import json
import csv
from django.http import HttpResponse

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    equip_filter = request.GET.get('equipment', '')

    if request.user.role == 'employee':
        tasks = Task.objects.filter(Q(assignee=request.user) | Q(assignee__isnull=True))
    else:
        tasks = Task.objects.all()

    if query:
        tasks = tasks.filter(Q(number__icontains=query) | Q(title__icontains=query) | Q(contact_info__icontains=query))
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    else:
        if not query:
            if request.user.role == 'employee':
                tasks = tasks.exclude(status='closed')

    if equip_filter:
        tasks = tasks.filter(equipment_type=equip_filter)

    # Сортировка по приоритету и свежести
    tasks = tasks.annotate(
        priority_weight=Case(
            When(priority='critical', then=Value(1)),
            When(priority='high', then=Value(2)),
            When(priority='medium', then=Value(3)),
            When(priority='low', then=Value(4)),
            default=Value(5),
            output_field=IntegerField()
        )
    ).order_by('priority_weight', '-created_at')

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
    
    if request.user.role == 'employee' and task.assignee and task.assignee != request.user:
        messages.error(request, 'Доступ запрещен. Вы можете просматривать только свои или неназначенные задачи.')
        return redirect('dashboard')

    if request.method == 'POST':
        old_status = task.get_status_display()
        old_priority = task.get_priority_display()
        old_assignee = task.assignee.username if task.assignee else "Не назначен"

        form = TaskForm(request.POST, request.FILES, instance=task, user=request.user)
        if form.is_valid():
            new_task = form.save(commit=False)
            
            changes = []
            if new_task.get_status_display() != old_status:
                changes.append(f"Статус: '{old_status}' → '{new_task.get_status_display()}'")
            if new_task.get_priority_display() != old_priority:
                changes.append(f"Приоритет: '{old_priority}' → '{new_task.get_priority_display()}'")
            new_assignee = new_task.assignee.username if new_task.assignee else "Не назначен"
            if new_assignee != old_assignee:
                changes.append(f"Ответственный: '{old_assignee}' → '{new_assignee}'")

            new_task.save()
            
            for change in changes:
                TaskLog.objects.create(task=new_task, user=request.user, action=change)

            messages.success(request, 'Задача успешно обновлена.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'tasks_app/task_detail.html', {'form': form, 'task': task})

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        text = request.POST.get('text')
        if text:
            TaskComment.objects.create(task=task, author=request.user, text=text)
            messages.success(request, 'Сообщение добавлено в чат.')
    return redirect('task_detail', pk=pk)

@login_required
def task_create(request):
    if request.user.role not in ['superuser', 'director']:
        messages.error(request, 'У вас нет прав для создания задач.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            import uuid
            task = form.save(commit=False)
            if not task.number:
                task.number = f"TSK-NEW-{uuid.uuid4().hex[:6].upper()}"
            task.save()
            TaskLog.objects.create(task=task, user=request.user, action="Задача создана")
            messages.success(request, 'Новая задача успешно создана.')
            return redirect('dashboard')
    else:
        form = TaskForm(user=request.user)
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
        form = UserCreateForm(request.POST, current_user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            if user.role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
            user.save()
            messages.success(request, f'Пользователь {user.username} успешно создан.')
            return redirect('user_management')
    else:
        form = UserCreateForm(current_user=request.user)
    return render(request, 'tasks_app/user_form.html', {'form': form, 'title': 'Создание пользователя'})

@login_required
def user_edit(request, pk):
    if request.user.role not in ['superuser', 'director']:
        return redirect('dashboard')
        
    user_to_edit = get_object_or_404(User, pk=pk)
    
    if user_to_edit.is_superuser and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав на редактирование суперпользователя.')
        return redirect('user_management')

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit, current_user=request.user)
        if form.is_valid():
            edited_user = form.save(commit=False)
            if form.cleaned_data.get('password'):
                edited_user.set_password(form.cleaned_data['password'])
            if edited_user.role == 'superuser':
                edited_user.is_superuser = True
                edited_user.is_staff = True
            else:
                edited_user.is_superuser = False
                edited_user.is_staff = False
            edited_user.save()
            messages.success(request, f'Данные пользователя {edited_user.username} обновлены.')
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user_to_edit, current_user=request.user)
    return render(request, 'tasks_app/user_form.html', {'form': form, 'title': 'Редактирование пользователя'})

@login_required
def user_delete(request, pk):
    if request.user.role not in ['superuser', 'director']:
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser and request.user.pk != user.pk:
         messages.error(request, 'Нельзя удалить суперпользователя.')
    elif user.pk == request.user.pk:
         messages.error(request, 'Нельзя удалить самого себя.')
    else:
         user.delete()
         messages.success(request, 'Пользователь удален.')
    return redirect('user_management')

@login_required
def stats(request):
    # Расчет среднего времени решения задач
    avg_time_data = []
    employees = User.objects.filter(role='employee')
    for emp in employees:
        tasks_res = Task.objects.filter(assignee=emp, status__in=['resolved', 'closed'])
        if tasks_res.exists():
            total_seconds = sum((t.updated_at - t.created_at).total_seconds() for t in tasks_res)
            avg_sec = total_seconds / tasks_res.count()
            days = int(avg_sec // 86400)
            hours = int((avg_sec % 86400) // 3600)
            avg_time_data.append({
                'name': f"{emp.first_name} {emp.last_name}".strip() or emp.username,
                'time': f"{days} д. {hours} ч." if days > 0 else f"{hours} ч.",
                'raw_sec': avg_sec
            })
    avg_time_data.sort(key=lambda x: x['raw_sec'])

    if request.user.role == 'employee':
        status_counts = list(Task.objects.filter(assignee=request.user).values('status').annotate(count=Count('id')))
        equip_counts = list(Task.objects.filter(assignee=request.user).values('equipment_type').annotate(count=Count('id')))
        
        last_30_days = timezone.now() - timedelta(days=30)
        recent_tasks = Task.objects.filter(assignee=request.user, created_at__gte=last_30_days).count()
        completed_tasks = Task.objects.filter(assignee=request.user, status__in=['resolved', 'closed']).count()
        
        context = {
            'status_counts': json.dumps(status_counts),
            'equip_counts': json.dumps(equip_counts),
            'recent_tasks': recent_tasks,
            'completed_tasks': completed_tasks,
            'avg_time_data': [d for d in avg_time_data if d['name'] == (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username)],
            'is_employee': True
        }
        return render(request, 'tasks_app/stats.html', context)
        
    if request.user.role not in ['superuser', 'director', 'manager']:
        return redirect('dashboard')
    
    status_counts = list(Task.objects.values('status').annotate(count=Count('id')))
    equip_counts = list(Task.objects.values('equipment_type').annotate(count=Count('id')))
    employee_stats = User.objects.filter(role='employee').annotate(task_count=Count('tasks')).order_by('-task_count')
    
    total_tasks = Task.objects.count()
    unassigned_tasks = Task.objects.filter(assignee__isnull=True).count()
    completed_all_time = Task.objects.filter(status__in=['resolved', 'closed']).count()

    context = {
        'status_counts': json.dumps(status_counts),
        'equip_counts': json.dumps(equip_counts),
        'employee_stats': employee_stats,
        'total_tasks': total_tasks,
        'unassigned_tasks': unassigned_tasks,
        'completed_all_time': completed_all_time,
        'avg_time_data': avg_time_data,
        'is_employee': False
    }
    return render(request, 'tasks_app/stats.html', context)

@login_required
def export_stats_csv(request):
    if request.user.role not in ['superuser', 'director', 'manager']:
        return redirect('dashboard')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="crm_stats_report.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    
    writer.writerow(['Отчет по задачам CRM'])
    writer.writerow(['Номер', 'Приоритет', 'Название', 'Оборудование', 'Статус', 'Ответственный', 'Создана', 'Обновлена'])
    
    tasks = Task.objects.all().order_by('-created_at')
    for t in tasks:
        assignee = t.assignee.username if t.assignee else 'Не назначен'
        writer.writerow([
            t.number, 
            t.get_priority_display(), 
            t.title, 
            t.get_equipment_type_display(), 
            t.get_status_display(), 
            assignee, 
            t.created_at.strftime("%Y-%m-%d %H:%M"), 
            t.updated_at.strftime("%Y-%m-%d %H:%M")
        ])
        
    return response