from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('superuser', 'Суперпользователь'),
        ('director', 'Руководитель'),
        ('manager', 'Менеджер'),
        ('editor', 'Редактор БЗ'),
        ('employee', 'Сотрудник'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('assigned', 'Назначена'),
        ('in_progress', 'В работе'),
        ('clarification', 'На уточнении'),
        ('resolved', 'Решена'),
        ('closed', 'Закрыта/Архив'),
    ]
    EQUIPMENT_CHOICES = [
        ('camera', 'Камера'),
        ('dvr', 'Регистратор'),
        ('intercom', 'Домофония'),
        ('switch', 'Коммутатор'),
        ('acs', 'СКУД'),
        ('ops', 'ОПС'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    number = models.CharField(max_length=50, unique=True, verbose_name="Номер задачи")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    description = models.TextField(verbose_name="Описание")
    contact_info = models.TextField(verbose_name="Контактные данные")
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_CHOICES, verbose_name="Тип оборудования")
    model_info = models.CharField(max_length=100, verbose_name="Модель")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="Ответственный")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Дедлайн")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(blank=True, verbose_name="Старые комментарии")
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True, verbose_name="Прикрепленный файл")

    def __str__(self):
        return f"{self.number} - {self.title}"
        
    @property
    def is_overdue(self):
        if self.deadline and self.status not in ['resolved', 'closed']:
            return timezone.now() > self.deadline
        return False

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(verbose_name="Текст сообщения")
    created_at = models.DateTimeField(auto_now_add=True)

class TaskLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255, verbose_name="Действие")
    created_at = models.DateTimeField(auto_now_add=True)

class KnowledgeBaseArticle(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название документа")
    description = models.TextField(blank=True, verbose_name="Краткое описание")
    file = models.FileField(upload_to='kb_files/', verbose_name="PDF Файл")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='kb_uploads')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)