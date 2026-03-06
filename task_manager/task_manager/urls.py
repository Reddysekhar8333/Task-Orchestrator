"""
URL configuration for task_manager project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='frontend-home'),
    path('auth/', TemplateView.as_view(template_name='auth.html'), name='frontend-auth'),
    path('tasks/', TemplateView.as_view(template_name='tasks.html'), name='frontend-tasks'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='frontend-dashboard'),
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('tasks.urls')),
]