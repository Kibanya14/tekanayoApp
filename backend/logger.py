"""
Structured Logging Module - Pour monitoring et debugging
Intègre les logs avec Sentry
"""

import logging
import json
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import traceback

class StructuredLogger:
    """Logger structuré pour production"""

    def __init__(self, app_name: str = "TekanayoApp"):
        self.app_name = app_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configurer le logger avec les handlers """
        logger = logging.getLogger(self.app_name)
        
        # Ne pas ajouter de handlers en double si le logger existe déjà
        if logger.handlers:
            return logger

        # Level par environnement
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logger.setLevel(getattr(logging, log_level))
        logger.propagate = False

        # Format structuré
        formatter = logging.Formatter(
            json.dumps({
                'timestamp': '%(asctime)s',
                'level': '%(levelname)s',
                'logger': '%(name)s',
                'message': '%(message)s'
            })
        )

        # Handler console (pour production)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler fichier rotatif (si en production)
        if os.getenv('FLASK_ENV') == 'production':
            log_dir = os.getenv('LOG_DIR', '/var/log/tekanayo')
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def info(self, message: str, **extra):
        """Log information"""
        self.logger.info(self._format_message(message, **extra))

    def warning(self, message: str, **extra):
        """Log warning"""
        self.logger.warning(self._format_message(message, **extra))

    def error(self, message: str, exc_info=False, **extra):
        """Log error"""
        if exc_info:
            extra['traceback'] = traceback.format_exc()
        self.logger.error(self._format_message(message, **extra), exc_info=exc_info)

    def critical(self, message: str, **extra):
        """Log critical issue"""
        self.logger.critical(self._format_message(message, **extra))

    def _format_message(self, message: str, **extra) -> str:
        """Formater le message avec les données extras"""
        if extra:
            return f"{message} | {json.dumps(extra)}"
        return message

    @staticmethod
    def log_request(request, response_code: int, elapsed_ms: float):
        """Log une requête HTTP"""
        logger = StructuredLogger().logger
        
        logger.info(
            "HTTP Request",
            extra={
                'method': request.method,
                'path': request.path,
                'status': response_code,
                'elapsed_ms': elapsed_ms,
                'user_agent': request.user_agent.string,
                'ip': request.remote_addr
            }
        )

    @staticmethod
    def log_database_query(query: str, duration_ms: float, rows_affected: int = None):
        """Log une requête database"""
        logger = StructuredLogger().logger
        
        extra = {
            'query_type': query.split()[0].upper(),
            'duration_ms': duration_ms,
        }
        if rows_affected is not None:
            extra['rows_affected'] = rows_affected
            
        logger.info("Database Query", extra=extra)

    @staticmethod
    def log_authentication(user_id: int, user_type: str, success: bool, method: str = 'login'):
        """Log authentification"""
        logger = StructuredLogger().logger
        
        if success:
            logger.info(
                f"Authentication successful - {user_type}",
                extra={'user_id': user_id, 'method': method}
            )
        else:
            logger.warning(
                f"Authentication failed - {user_type}",
                extra={'user_id': user_id, 'method': method}
            )

    @staticmethod
    def log_file_operation(operation: str, file_name: str, file_size_mb: float, success: bool):
        """Log une opération de fichier"""
        logger = StructuredLogger().logger
        
        if success:
            logger.info(
                f"File operation: {operation}",
                extra={'file': file_name, 'size_mb': file_size_mb}
            )
        else:
            logger.error(
                f"File operation failed: {operation}",
                extra={'file': file_name, 'size_mb': file_size_mb}
            )

    @staticmethod
    def log_payment(order_id: int, amount: float, status: str, gateway: str):
        """Log une transaction de paiement"""
        logger = StructuredLogger().logger
        
        level = 'info' if status == 'success' else 'warning'
        getattr(logger, level)(
            f"Payment {status}",
            extra={'order_id': order_id, 'amount': amount, 'gateway': gateway}
        )

    @staticmethod
    def log_security_event(event_type: str, user_id: int = None, details: str = None):
        """Log un événement de sécurité"""
        logger = StructuredLogger().logger
        
        extra = {'event_type': event_type}
        if user_id:
            extra['user_id'] = user_id
        if details:
            extra['details'] = details
            
        logger.warning(f"SECURITY EVENT: {event_type}", extra=extra)


def setup_sentry(app):
    """Configurer Sentry pour les erreurs en production"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.1,  # 10% des transactions
                environment=os.getenv('FLASK_ENV', 'development'),
                release="1.0.0"
            )
            
            logger = StructuredLogger()
            logger.info("✅ Sentry initialized for error tracking")
            
        except ImportError:
            print("⚠️ sentry-sdk not installed, skipping Sentry setup")
    else:
        print("⚠️ SENTRY_DSN not configured")


def log_before_request(logger):
    """Decorator pour log les requêtes"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            from flask import request, g
            import time
            
            g.start_time = time.time()
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_after_request(logger):
    """Decorator pour log les réponses"""
    def decorator(response):
        from flask import request, g
        import time
        
        if hasattr(g, 'start_time'):
            elapsed_ms = (time.time() - g.start_time) * 1000
            StructuredLogger.log_request(request, response.status_code, elapsed_ms)
        
        return response
    return decorator


class AppLogger:
    """App logger pour l'intégration Flask"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = StructuredLogger()
        return cls._instance
    
    def get(self):
        return self.logger


# Utility functions
def log_app_startup(app_name: str, version: str):
    """Log au démarage de l'application"""
    logger = StructuredLogger()
    logger.info(
        f"Application starting - {app_name}",
        extra={
            'version': version,
            'environment': os.getenv('FLASK_ENV', 'development'),
            'timestamp': datetime.utcnow().isoformat()
        }
    )


def log_app_shutdown(app_name: str, uptime_seconds: int):
    """Log à l'arrêt de l'application"""
    logger = StructuredLogger()
    logger.info(
        f"Application shutting down - {app_name}",
        extra={
            'uptime_seconds': uptime_seconds,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
