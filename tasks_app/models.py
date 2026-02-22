from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('superuser', 'Суперпользователь'),
        ('director', 'Руководитель'),
        ('manager', 'Менеджер'),
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
    
    title = models.CharField(max_length=200, verbose_name="Название")
    number = models.CharField(max_length=50, unique=True, verbose_name="Номер задачи")
    description = models.TextField(verbose_name="Описание")
    contact_info = models.TextField(verbose_name="Контактные данные")
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_CHOICES, verbose_name="Тип оборудования")
    model_info = models.CharField(max_length=100, verbose_name="Модель")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="Ответственный")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(blank=True, verbose_name="Комментарии")
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True, verbose_name="Прикрепленный файл")

    def __str__(self):
        return f"{self.number} - {self.title}"