from django.db import models
from django.db.models import Q
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer
from .tasks import process_task_file


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority', 'status']

    def get_queryset(self):
        """Optimized queryset scoped to the authenticated user."""
        queryset = Task.objects.filter(user=self.request.user).select_related('user')

        status_filter = self.request.query_params.get('status')
        task_type = self.request.query_params.get('task_type')
        priority = self.request.query_params.get('priority')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get task statistics for dashboard in a single aggregate query."""
        stats = self.get_queryset().aggregate(
            total=models.Count('id'),
            pending=models.Count('id', filter=Q(status='PENDING')),
            processing=models.Count('id', filter=Q(status='PROCESSING')),
            completed=models.Count('id', filter=Q(status='COMPLETED')),
            failed=models.Count('id', filter=Q(status='FAILED')),
        )

        recent_tasks = self.get_queryset()[:5]

        return Response(
            {
                'stats': stats,
                'recent_tasks': TaskSerializer(recent_tasks, many=True).data,
            }
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a task if it's pending or processing."""
        task = self.get_object()
        if task.status in ['PENDING', 'PROCESSING']:
            task.status = 'CANCELLED'
            task.save(update_fields=['status'])
            return Response({'status': 'task cancelled'})

        return Response(
            {'error': f'Cannot cancel task in {task.status} state'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        try:
            # Pass task.id as a string for JSON serialization in the broker
            process_task_file.delay(str(task.id))
        except Exception:
            # Log the error here if you have a logger configured
            # This prevents a 500 error if Redis/RabbitMQ is down
            pass