from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'contact_info', 'equipment_type', 'model_info', 'status', 'assignee', 'comments', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'equipment_type': forms.Select(attrs={'class': 'form-select'}),
            'model_info': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }