@echo off
echo Starting Django Backend...
start cmd /k "python manage.py runserver"

echo Starting React Frontend...
cd frontend
start cmd /k "npm run dev"

echo Both servers are running!