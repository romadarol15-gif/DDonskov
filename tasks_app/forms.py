from django import forms
from .models import Task, User
from django.db.models import Q

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'priority', 'description', 'contact_info', 'equipment_type', 'model_info', 'status', 'assignee', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select fw-bold text-dark bg-warning bg-opacity-75'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'equipment_type': forms.Select(attrs={'class': 'form-select'}),
            'model_info': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select fw-bold'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.role == 'employee':
                self.fields['assignee'].queryset = User.objects.filter(id=user.id)
            else:
                self.fields['assignee'].queryset = User.objects.filter(role='employee')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'role': 'Роль'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if current_user and current_user.role != 'superuser':
            choices = list(User.ROLE_CHOICES)
            self.fields['role'].choices = [c for c in choices if c[0] != 'superuser']

class UserEditForm(UserCreateForm):
    password = forms.CharField(label="Новый пароль (оставьте пустым, если не хотите менять)", required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)