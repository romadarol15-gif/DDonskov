@echo off
echo =========================================
echo Updating CRM System Database and Files...
echo =========================================

echo Checking virtual environment...
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Applying database migrations...
python manage.py makemigrations tasks_app
python manage.py migrate

echo Updating test data...
python setup_data.py

echo =========================================
echo Update Complete! You can now run run.bat
echo =========================================
pause