from celery import shared_task
import time

@shared_task
def process_task_file(task_id):
    # This simulates heavy processing (like AI analysis or file compression)
    print(f"Starting background processing for Task ID: {task_id}")
    time.sleep(10) # Simulate a 10-second heavy job
    print(f"Task {task_id} processing complete!")
    return True