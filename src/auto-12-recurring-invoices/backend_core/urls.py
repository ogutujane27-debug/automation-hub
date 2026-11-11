import os
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.views.static import serve

def serve_react_app(request, path=''):
    dist_dir = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
    if path:
        file_path = os.path.join(dist_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return serve(request, path, document_root=dist_dir)
    
    index_file_path = os.path.join(dist_dir, 'index.html')
    if os.path.exists(index_file_path):
        with open(index_file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    return HttpResponse("React build not found. Run 'npm run build' inside the frontend folder.", status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recurring_invoices.urls')),
    path('<path:path>', serve_react_app),
    path('', serve_react_app),
]