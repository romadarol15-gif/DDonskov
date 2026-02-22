import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from tasks_app.models import User, Task

def create_data():
    users = [
        {'username': 'admin', 'role': 'superuser', 'password': '123'},
        {'username': 'director', 'role': 'director', 'password': '123'},
        {'username': 'manager', 'role': 'manager', 'password': '123'},
        {'username': 'editor_kb', 'role': 'editor', 'password': '123'},
        {'username': 'emp1', 'role': 'employee', 'password': '123'},
        {'username': 'emp2', 'role': 'employee', 'password': '123'},
        {'username': 'emp3', 'role': 'employee', 'password': '123'},
    ]
    
    for u in users:
        if not User.objects.filter(username=u['username']).exists():
            if u['role'] == 'superuser':
                user = User.objects.create_superuser(username=u['username'], password=u['password'], email=f"{u['username']}@test.com")
            else:
                user = User.objects.create_user(username=u['username'], password=u['password'], email=f"{u['username']}@test.com")
            user.role = u['role']
            user.save()
    
    print("Users created.")

    equipments = ['camera', 'dvr', 'intercom', 'switch', 'acs', 'ops']
    priorities = ['low', 'medium', 'high', 'critical']
    emp = User.objects.get(username='emp1')
    
    for idx, eq in enumerate(equipments):
        for i in range(2):
            num = f"TSK-{eq.upper()}-{i+1}"
            if not Task.objects.filter(number=num).exists():
                Task.objects.create(
                    title=f"Тестовая задача {eq} {i+1}",
                    number=num,
                    priority=random.choice(priorities),
                    description="Описание поломки или задачи по настройке. Клиент жалуется на неисправность.",
                    contact_info="Иван Иванов, +7 999 123 45 67",
                    equipment_type=eq,
                    model_info="TestModel-X",
                    status='new' if i == 0 else 'assigned',
                    assignee=None if i == 0 else emp,
                    comments="Первичный осмотр требуется."
                )
    print("Tasks created.")

if __name__ == '__main__':
    create_data()