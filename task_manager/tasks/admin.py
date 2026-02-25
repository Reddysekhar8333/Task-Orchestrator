from django.contrib import admin
from .models import Task

# Register your models here.

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    list_filter = ('status',) # This uses the index we created for optimization!