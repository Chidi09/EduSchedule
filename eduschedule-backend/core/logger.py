# eduschedule-backend/core/logger.py
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger
from functools import wraps
import traceback
import time

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context fields."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add service information
        log_record['service'] = 'eduschedule-backend'
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id

        # Add exception information if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_record['duration_ms'] = record.duration

        # Ensure level is properly set
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add thread information
        import threading
        record.thread_name = threading.current_thread().name

        # Add process information
        record.process_id = os.getpid()

        return True

class PerformanceLogger:
    """Context manager for logging performance metrics."""

    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds

        if exc_type:
            self.logger.error(
                f"Failed {self.operation}",
                extra={
                    'duration': duration,
                    'operation': self.operation,
                    'success': False
                }
            )
        else:
            self.logger.log(
                self.level,
                f"Completed {self.operation}",
                extra={
                    'duration': duration,
                    'operation': self.operation,
                    'success': True
                }
            )

def setup_logging() -> logging.Logger:
    """Configure production-ready structured logging."""

    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    log_file = os.getenv('LOG_FILE', None)

    # Create root logger
    logger = logging.getLogger()

    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []

    # Set log level
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatters
    if log_format == 'json':
        formatter = CustomJsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.addFilter(ContextFilter())
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to create file handler for {log_file}: {e}")

    # Configure third-party loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('celery').setLevel(logging.INFO)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def log_api_call(func):
    """Decorator to log API calls with request/response information."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(f"api.{func.__module__}.{func.__name__}")

        # Extract request information
        request_info = {}
        for arg in args:
            if hasattr(arg, 'method') and hasattr(arg, 'url'):  # FastAPI Request
                request_info = {
                    'method': arg.method,
                    'path': str(arg.url.path),
                    'query_params': dict(arg.query_params),
                    'user_agent': arg.headers.get('user-agent', 'unknown')
                }
                break

        with PerformanceLogger(logger, f"API {func.__name__}"):
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    f"API call successful: {func.__name__}",
                    extra={'request': request_info, 'function': func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"API call failed: {func.__name__}",
                    extra={
                        'request': request_info,
                        'function': func.__name__,
                        'error': str(e)
                    }
                )
                raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(f"api.{func.__module__}.{func.__name__}")

        with PerformanceLogger(logger, f"API {func.__name__}"):
            try:
                result = func(*args, **kwargs)
                logger.info(f"API call successful: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"API call failed: {func.__name__}: {str(e)}")
                raise

    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def log_task_execution(func):
    """Decorator to log Celery task execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(f"task.{func.__module__}.{func.__name__}")

        with PerformanceLogger(logger, f"Task {func.__name__}"):
            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"Task completed successfully: {func.__name__}",
                    extra={'args': str(args)[:200], 'kwargs': str(kwargs)[:200]}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Task failed: {func.__name__}",
                    extra={
                        'args': str(args)[:200],
                        'kwargs': str(kwargs)[:200],
                        'error': str(e)
                    }
                )
                raise

    return wrapper

def log_database_operation(operation_type: str):
    """Decorator to log database operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f"database.{func.__module__}.{func.__name__}")

            with PerformanceLogger(logger, f"DB {operation_type}"):
                try:
                    result = func(*args, **kwargs)
                    logger.info(f"Database {operation_type} successful")
                    return result
                except Exception as e:
                    logger.error(f"Database {operation_type} failed: {str(e)}")
                    raise

        return wrapper
    return decorator

class SecurityLogger:
    """Specialized logger for security events."""

    def __init__(self):
        self.logger = get_logger("security")

    def log_authentication_success(self, user_id: str, method: str, ip_address: Optional[str] = None):
        """Log successful authentication."""
        self.logger.info(
            "Authentication successful",
            extra={
                'event_type': 'auth_success',
                'user_id': user_id,
                'auth_method': method,
                'ip_address': ip_address,
                'security_event': True
            }
        )

    def log_authentication_failure(self, username: str, method: str, reason: str, ip_address: Optional[str] = None):
        """Log failed authentication attempt."""
        self.logger.warning(
            "Authentication failed",
            extra={
                'event_type': 'auth_failure',
                'username': username,
                'auth_method': method,
                'failure_reason': reason,
                'ip_address': ip_address,
                'security_event': True
            }
        )

    def log_authorization_failure(self, user_id: str, resource: str, action: str, ip_address: Optional[str] = None):
        """Log authorization failure."""
        self.logger.warning(
            "Authorization denied",
            extra={
                'event_type': 'authz_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'ip_address': ip_address,
                'security_event': True
            }
        )

    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any], ip_address: Optional[str] = None):
        """Log suspicious activity."""
        self.logger.error(
            "Suspicious activity detected",
            extra={
                'event_type': 'suspicious_activity',
                'user_id': user_id,
                'activity': activity,
                'details': details,
                'ip_address': ip_address,
                'security_event': True
            }
        )

# Initialize logging when module is imported
logger = setup_logging()

# Create specialized loggers
security_logger = SecurityLogger()

# Export main components
__all__ = [
    'setup_logging',
    'get_logger',
    'log_api_call',
    'log_task_execution',
    'log_database_operation',
    'PerformanceLogger',
    'SecurityLogger',
    'security_logger',
    'logger'
]
