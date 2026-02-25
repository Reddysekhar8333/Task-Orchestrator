from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Task
from .serializers import TaskSerializer, TaskStatusSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'task_type', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority', 'status']
    
    def get_queryset(self):
        """Optimized queryset with select_related for user"""
        return Task.objects.filter(user=self.request.user).select_related('user')
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get task statistics for dashboard - optimized with single query"""
        user = request.user
        
        # Single query with aggregation
        stats = Task.objects.filter(user=user).aggregate(
            total=models.Count('id'),
            pending=models.Count('id', filter=Q(status='PENDING')),
            processing=models.Count('id', filter=Q(status='PROCESSING')),
            completed=models.Count('id', filter=Q(status='COMPLETED')),
            failed=models.Count('id', filter=Q(status='FAILED')),
        )
        
        # Get recent tasks
        recent_tasks = self.get_queryset()[:5]
        
        return Response({
            'stats': stats,
            'recent_tasks': TaskSerializer(recent_tasks, many=True).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a task if it's pending or processing"""
        task = self.get_object()
        if task.status in ['PENDING', 'PROCESSING']:
            task.status = 'CANCELLED'
            task.save()
            return Response({'status': 'task cancelled'})
        return Response(
            {'error': f'Cannot cancel task in {task.status} state'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get tasks grouped by status - optimized"""
        status = request.query_params.get('status', None)
        if status:
            tasks = self.get_queryset().filter(status=status)
        else:
            tasks = self.get_queryset()
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)