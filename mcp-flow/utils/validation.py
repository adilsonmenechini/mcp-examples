from typing import Dict, Any, List, Optional, Union, Type, Callable
from pydantic import BaseModel, ValidationError
import re
from .errors import ValidationError as MCPValidationError


class ValidationResult:
    def __init__(self, valid: bool, errors: Optional[List[str]] = None):
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def add_error(self, error: str) -> None:
        self.valid = False
        self.errors.append(error)

    def merge(self, other: "ValidationResult") -> None:
        if not other.valid:
            self.valid = False
            self.errors.extend(other.errors)


class Validator:
    """Base validator class"""

    def validate(self, value: Any) -> ValidationResult:
        raise NotImplementedError("Validators must implement validate()")


class TypeValidator(Validator):
    """Validate value type"""

    def __init__(self, expected_type: Type):
        self.expected_type = expected_type

    def validate(self, value: Any) -> ValidationResult:
        if not isinstance(value, self.expected_type):
            return ValidationResult(
                False,
                [
                    f"Expected type {self.expected_type.__name__}, got {type(value).__name__}"
                ],
            )
        return ValidationResult(True)


class RangeValidator(Validator):
    """Validate numeric range"""

    def __init__(
        self, min_value: Optional[float] = None, max_value: Optional[float] = None
    ):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Union[int, float]) -> ValidationResult:
        if not isinstance(value, (int, float)):
            return ValidationResult(False, ["Value must be numeric"])

        result = ValidationResult(True)
        if self.min_value is not None and value < self.min_value:
            result.add_error(f"Value must be >= {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            result.add_error(f"Value must be <= {self.max_value}")
        return result


class RegexValidator(Validator):
    """Validate string against regex pattern"""

    def __init__(self, pattern: str, description: str = None):
        self.pattern = re.compile(pattern)
        self.description = description or f"Must match pattern {pattern}"

    def validate(self, value: str) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult(False, ["Value must be a string"])
        if not self.pattern.match(value):
            return ValidationResult(False, [self.description])
        return ValidationResult(True)


class ListValidator(Validator):
    """Validate list elements"""

    def __init__(self, element_validator: Validator):
        self.element_validator = element_validator

    def validate(self, value: List[Any]) -> ValidationResult:
        if not isinstance(value, list):
            return ValidationResult(False, ["Value must be a list"])

        result = ValidationResult(True)
        for i, element in enumerate(value):
            element_result = self.element_validator.validate(element)
            if not element_result:
                for error in element_result.errors:
                    result.add_error(f"Element {i}: {error}")
        return result


class DictValidator(Validator):
    """Validate dictionary fields"""

    def __init__(
        self, field_validators: Dict[str, Validator], required_fields: List[str] = None
    ):
        self.field_validators = field_validators
        self.required_fields = set(required_fields or [])

    def validate(self, value: Dict[str, Any]) -> ValidationResult:
        if not isinstance(value, dict):
            return ValidationResult(False, ["Value must be a dictionary"])

        result = ValidationResult(True)

        # Check required fields
        missing_fields = self.required_fields - set(value.keys())
        if missing_fields:
            for field in missing_fields:
                result.add_error(f"Missing required field: {field}")
            return result

        # Validate each field
        for field, validator in self.field_validators.items():
            if field in value:
                field_result = validator.validate(value[field])
                if not field_result:
                    for error in field_result.errors:
                        result.add_error(f"Field {field}: {error}")

        return result


class CustomValidator(Validator):
    """Validate using custom function"""

    def __init__(
        self,
        func: Callable[[Any], Union[bool, ValidationResult]],
        error_message: str = None,
    ):
        self.func = func
        self.error_message = error_message

    def validate(self, value: Any) -> ValidationResult:
        result = self.func(value)
        if isinstance(result, ValidationResult):
            return result
        elif isinstance(result, bool):
            return ValidationResult(
                result,
                [self.error_message] if not result and self.error_message else None,
            )
        else:
            return ValidationResult(False, ["Invalid validator function result"])


def validate_model(data: Dict[str, Any], model: Type[BaseModel]) -> Dict[str, Any]:
    """Validate data against Pydantic model"""
    try:
        validated = model(**data)
        return validated.dict()
    except ValidationError as e:
        errors = []
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(f"{location}: {error['msg']}")
        raise MCPValidationError(
            message="Validation failed", details={"errors": errors}
        )


def validate_config(config: Dict[str, Any], validators: Dict[str, Validator]) -> None:
    """Validate configuration using validators"""
    result = ValidationResult(True)

    for key, validator in validators.items():
        if key in config:
            key_result = validator.validate(config[key])
            if not key_result:
                for error in key_result.errors:
                    result.add_error(f"Configuration {key}: {error}")

    if not result:
        raise MCPValidationError(
            message="Configuration validation failed", details={"errors": result.errors}
        )
