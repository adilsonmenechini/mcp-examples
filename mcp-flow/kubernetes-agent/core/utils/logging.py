import logging
import json
from datetime import datetime


class CustomJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if they exist
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(
    name: str, log_file: str = None, level: int = logging.INFO
) -> logging.Logger:
    """Setup a JSON-formatted logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create JSON formatter
    formatter = CustomJsonFormatter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_operation(logger: logging.Logger, operation: str, **kwargs):
    """Decorator to log operation details"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    f"{operation} completed successfully",
                    extra={
                        "extra_data": {
                            "operation": operation,
                            "duration_ms": (
                                datetime.utcnow() - start_time
                            ).total_seconds()
                            * 1000,
                            "success": True,
                            "params": kwargs,
                        }
                    },
                )
                return result
            except Exception as e:
                logger.error(
                    f"{operation} failed",
                    extra={
                        "extra_data": {
                            "operation": operation,
                            "duration_ms": (
                                datetime.utcnow() - start_time
                            ).total_seconds()
                            * 1000,
                            "success": False,
                            "error": str(e),
                            "params": kwargs,
                        }
                    },
                )
                raise

        return wrapper

    return decorator
