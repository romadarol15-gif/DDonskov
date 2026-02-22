@echo off
call venv\Scripts\activate.bat
echo Starting server...
python manage.py runserver
pause