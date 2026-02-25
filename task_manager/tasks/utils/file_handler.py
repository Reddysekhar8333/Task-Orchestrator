import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

class FileHandler:
    @staticmethod
    def save_uploaded_file(uploaded_file, task_id, file_type='input'):
        """Save uploaded file locally (Phase 1)"""
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{file_type}_{task_id}{ext}"
        
        # Save to local storage
        path = default_storage.save(
            f'tasks/{task_id}/{filename}',
            ContentFile(uploaded_file.read())
        )
        
        return {
            'filename': filename,
            'path': path,
            'url': default_storage.url(path),
            'size': uploaded_file.size
        }
    
    @staticmethod
    def validate_file_size(uploaded_file, max_size_mb=100):
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            raise ValueError(f"File size exceeds {max_size_mb}MB limit")
        return True
    
    @staticmethod
    def validate_file_type(uploaded_file, allowed_types):
        """Validate file type"""
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed_types:
            raise ValueError(f"File type {ext} not allowed. Allowed: {allowed_types}")
        return True