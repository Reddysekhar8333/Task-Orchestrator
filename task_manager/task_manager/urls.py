"""
URL configuration for task_manager project.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView

def healthz(_request):
    """Simple process-level health endpoint for container checks."""
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    # path('healthz', lambda r: HttpResponse("OK")),
    path('healthz', healthz, name='healthz'),
    path('', TemplateView.as_view(template_name='index.html'), name='frontend-home'),
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('tasks.urls')),
]