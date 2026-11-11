import os
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings

def serve_react_app(request):
    index_file_path = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
    if os.path.exists(index_file_path):
        with open(index_file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    return HttpResponse("React build not found. Run 'npm run build' inside the frontend folder.", status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recurring_invoices.urls')),
    path('', serve_react_app),  # This catches the root URL and serves your React app
]