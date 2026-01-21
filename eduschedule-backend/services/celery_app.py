# eduschedule-backend/services/celery_app.py
from celery import Celery
from kombu import Queue
from core.config import get_settings
from core.logger import get_logger
import os

settings = get_settings()
logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "eduschedule_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'services.tasks',
        'services.email_tasks',
        'services.scheduler_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,

    # Timezone
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,

    # Task execution
    task_soft_time_limit=settings.TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.TASK_HARD_TIME_LIMIT,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Retry configuration
    task_default_retry_delay=settings.TASK_RETRY_DELAY,
    task_max_retries=settings.TASK_MAX_RETRIES,

    # Task routing
    task_routes={
        'services.tasks.generate_timetable_task': {'queue': 'high_priority'},
        'services.tasks.send_email_alert': {'queue': 'low_priority'},
        'services.tasks.cleanup_old_data': {'queue': 'maintenance'},
        'services.tasks.backup_database': {'queue': 'maintenance'},
    },

    # Queue definitions
    task_queues=(
        Queue('high_priority', routing_key='high_priority'),
        Queue('low_priority', routing_key='low_priority'),
        Queue('maintenance', routing_key='maintenance'),
        Queue('default', routing_key='default'),
    ),
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Worker settings
    worker_disable_rate_limits=False,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Beat scheduler (for periodic tasks)
    beat_schedule={
        'cleanup-old-timetables': {
            'task': 'services.tasks.cleanup_old_data',
            'schedule': 86400.0,  # Run daily
            'options': {'queue': 'maintenance'}
        },
        'health-check': {
            'task': 'services.tasks.health_check_task',
            'schedule': 300.0,  # Run every 5 minutes
            'options': {'queue': 'maintenance'}
        },
        'backup-database': {
            'task': 'services.tasks.backup_database',
            'schedule': 21600.0,  # Run every 6 hours
            'options': {'queue': 'maintenance'}
        },
    },
    beat_schedule_filename='celerybeat-schedule',

    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,

    # Security
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Task annotations for specific task configurations
celery_app.conf.task_annotations = {
    'services.tasks.generate_timetable_task': {
        'rate_limit': '10/m',  # Maximum 10 timetable generations per minute
        'soft_time_limit': 1800,  # 30 minutes soft limit
        'time_limit': 3600,  # 1 hour hard limit
        'retry_kwargs': {'max_retries': 3, 'countdown': 60},
        'bind': True,
    },
    'services.tasks.send_email_alert': {
        'rate_limit': '100/m',  # Maximum 100 emails per minute
        'soft_time_limit': 30,
        'time_limit': 60,
        'retry_kwargs': {'max_retries': 5, 'countdown': 30},
    },
    'services.tasks.cleanup_old_data': {
        'soft_time_limit': 300,  # 5 minutes
        'time_limit': 600,  # 10 minutes
        'retry_kwargs': {'max_retries': 1, 'countdown': 3600},  # Retry after 1 hour
    }
}

# Custom error handler
@celery_app.task(bind=True)
def error_handler(self, uuid, data, traceback):
    """Custom error handler for failed tasks."""
    logger.error(f"Task {uuid} failed: {data}", extra={
        'task_id': uuid,
        'error_data': data,
        'traceback': traceback
    })

# Health check for Celery workers
@celery_app.task(name='celery.ping')
def ping():
    """Ping task to check if workers are alive."""
    return 'pong'

# Configure logging for Celery
if not settings.is_testing:
    from core.logger import setup_logging
    setup_logging()

logger.info("Celery application configured successfully")

# Export the app
__all__ = ['celery_app']
