from typing import Dict, Any, Optional
import traceback
import json
from enum import Enum


class ErrorCode(Enum):
    # Common errors (1-99)
    UNKNOWN_ERROR = 1
    CONFIGURATION_ERROR = 2
    INITIALIZATION_ERROR = 3
    VALIDATION_ERROR = 4
    RESOURCE_NOT_FOUND = 5
    OPERATION_TIMEOUT = 6
    PERMISSION_DENIED = 7

    # API/Network errors (100-199)
    API_ERROR = 100
    NETWORK_ERROR = 101
    CONNECTION_ERROR = 102
    AUTHENTICATION_ERROR = 103
    REQUEST_ERROR = 104
    RESPONSE_ERROR = 105

    # Data errors (200-299)
    DATA_ERROR = 200
    SERIALIZATION_ERROR = 201
    DESERIALIZATION_ERROR = 202
    SCHEMA_ERROR = 203
    DATA_VALIDATION_ERROR = 204

    # Cache errors (300-399)
    CACHE_ERROR = 300
    CACHE_MISS = 301
    CACHE_FULL = 302
    CACHE_INVALID = 303

    # Resource errors (400-499)
    RESOURCE_ERROR = 400
    RESOURCE_BUSY = 401
    RESOURCE_EXHAUSTED = 402
    RESOURCE_LOCKED = 403
    RESOURCE_UNAVAILABLE = 404


class MCPError(Exception):
    """Base exception class for MCP servers"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        error_dict = {
            "code": self.code.value,
            "type": self.code.name,
            "message": self.message,
            "details": self.details,
        }

        if self.original_error:
            error_dict["original_error"] = {
                "type": type(self.original_error).__name__,
                "message": str(self.original_error),
                "traceback": traceback.format_exc(),
            }

        return error_dict

    def to_json(self) -> str:
        """Convert error to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> "MCPError":
        """Create MCPError from another exception"""
        return cls(message=str(exc), code=code, details=details, original_error=exc)


class ConfigurationError(MCPError):
    """Configuration related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, code=ErrorCode.CONFIGURATION_ERROR, details=details
        )


class ValidationError(MCPError):
    """Data validation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, code=ErrorCode.VALIDATION_ERROR, details=details
        )


class ResourceError(MCPError):
    """Resource related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, code=ErrorCode.RESOURCE_ERROR, details=details
        )


class APIError(MCPError):
    """API related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=ErrorCode.API_ERROR, details=details)


def handle_error(error: Exception) -> Dict[str, Any]:
    """Convert any error to a standardized error response"""
    if isinstance(error, MCPError):
        return {"status": "error", "error": error.to_dict()}
    else:
        mcp_error = MCPError.from_exception(error)
        return {"status": "error", "error": mcp_error.to_dict()}


def error_handler(func):
    """Decorator to handle errors in a consistent way"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return handle_error(e)

    return wrapper
