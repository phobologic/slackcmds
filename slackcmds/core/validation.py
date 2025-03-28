"""
Parameter validation utilities.

This module provides utilities for validating command parameters,
including common validation functions and parameter definition classes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, TypeVar, Generic
import re
import inspect
from functools import partial

from .response import CommandResponse


# Type definitions
ValidatorFunc = Callable[[str], Optional[str]]
TypeValidatorFunc = Callable[[str], Tuple[Any, Optional[str]]]


# Type-specific validation functions for standard types
def _validate_integer(value: str) -> Tuple[Optional[int], Optional[str]]:
    """Validate that a value is an integer.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    try:
        return int(value), None
    except ValueError:
        return None, f"Invalid value for integer: {value}"


def _validate_float(value: str) -> Tuple[Optional[float], Optional[str]]:
    """Validate that a value is a float.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    try:
        return float(value), None
    except ValueError:
        return None, f"Invalid value for float: {value}"


def _validate_boolean(value: str) -> Tuple[Optional[bool], Optional[str]]:
    """Validate that a value is a boolean.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    value_lower = value.lower()
    if value_lower in ("yes", "true", "1", "y", "t"):
        return True, None
    elif value_lower in ("no", "false", "0", "n", "f"):
        return False, None
    else:
        return None, f"Invalid boolean value: {value}. Expected yes/no, true/false, 1/0, etc."


def _validate_user_id(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate that a value is a Slack user ID.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    if not value.startswith("<@U") and not value.startswith("U"):
        return None, f"Invalid user ID: {value}. Expected format: <@UXXXXXXXX> or UXXXXXXXX"
    
    # Extract just the ID if in the format <@UXXXX>
    if value.startswith("<@") and value.endswith(">"):
        return value[2:-1], None
    
    return value, None


def _validate_channel_id(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate that a value is a Slack channel ID.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    if not value.startswith("<#C") and not value.startswith("C"):
        return None, f"Invalid channel ID: {value}. Expected format: <#CXXXXXXXX> or CXXXXXXXX"
    
    # Extract just the ID if in the format <#CXXXX>
    if value.startswith("<#") and value.endswith(">"):
        return value[2:-1].split("|")[0], None  # Handle <#Cxxxx|channel-name>
    
    return value, None


def _validate_email(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate that a value is an email address.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    # Check for Slack's mailto format: <mailto:email@example.com|email@example.com>
    mailto_regex = r"^<mailto:([^|]+)\|([^>]+)>$"
    mailto_match = re.match(mailto_regex, value)
    
    if mailto_match:
        # Extract the email from the mailto format
        email = mailto_match.group(2)  # Use the display part after |
    else:
        email = value
    
    # Basic email validation
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        return None, f"Invalid email address: {email}"
    
    return email, None


def _validate_url(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate that a value is a URL.
    
    Args:
        value: The value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    # Handle Slack URL format: <https://example.com|example.com>
    url_slack_regex = r"^<(https?://[^|]+)\|([^>]+)>$"
    url_slack_match = re.match(url_slack_regex, value)
    
    if url_slack_match:
        # Extract the URL from Slack's format
        url = url_slack_match.group(1)  # Use the actual URL part before |
    else:
        url = value
    
    # Basic URL validation
    url_regex = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    if not re.match(url_regex, url):
        return None, f"Invalid URL: {url}"
    
    return url, None


def _validate_choice(value: str, choices: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str]]:
    """Validate that a value is one of the allowed choices.
    
    Args:
        value: The value to validate.
        choices: List of allowed choices.
        
    Returns:
        tuple: (validated_value, error_message)
    """
    if choices is None:
        return None, "No choices specified for choice parameter"
    
    if value not in choices:
        return None, f"Invalid choice: {value}. Valid options: {', '.join(choices)}"
    
    return value, None


# Common validator functions
def min_length(min_len: int) -> ValidatorFunc:
    """Validator for minimum string length.
    
    Args:
        min_len: The minimum allowed length.
        
    Returns:
        A validator function.
    """
    def validator(value: str) -> Optional[str]:
        if len(value) < min_len:
            return f"Value must be at least {min_len} characters long"
        return None
    return validator


def max_length(max_len: int) -> ValidatorFunc:
    """Validator for maximum string length.
    
    Args:
        max_len: The maximum allowed length.
        
    Returns:
        A validator function.
    """
    def validator(value: str) -> Optional[str]:
        if len(value) > max_len:
            return f"Value must be at most {max_len} characters long"
        return None
    return validator


def pattern(regex: str, error_msg: Optional[str] = None) -> ValidatorFunc:
    """Validator for regex pattern matching.
    
    Args:
        regex: The regex pattern to match.
        error_msg: Custom error message.
        
    Returns:
        A validator function.
    """
    compiled_regex = re.compile(regex)
    def validator(value: str) -> Optional[str]:
        if not compiled_regex.match(value):
            return error_msg or f"Value does not match required pattern"
        return None
    return validator


def min_value(min_val: Union[int, float]) -> ValidatorFunc:
    """Validator for minimum numeric value.
    
    Args:
        min_val: The minimum allowed value.
        
    Returns:
        A validator function.
    """
    def validator(value: str) -> Optional[str]:
        try:
            num_value = float(value)
            if num_value < min_val:
                return f"Value must be at least {min_val}"
        except ValueError:
            return "Value must be a number"
        return None
    return validator


def max_value(max_val: Union[int, float]) -> ValidatorFunc:
    """Validator for maximum numeric value.
    
    Args:
        max_val: The maximum allowed value.
        
    Returns:
        A validator function.
    """
    def validator(value: str) -> Optional[str]:
        try:
            num_value = float(value)
            if num_value > max_val:
                return f"Value must be at most {max_val}"
        except ValueError:
            return "Value must be a number"
        return None
    return validator


class ValidatorRegistry:
    """Registry for custom validators.
    
    This class maintains a collection of validator functions that can be
    applied to parameter values.
    """
    
    def __init__(self) -> None:
        """Initialize a new validator registry."""
        self._validators: Dict[str, ValidatorFunc] = {}
    
    def register(self, name: str, validator: ValidatorFunc) -> None:
        """Register a validator function.
        
        Args:
            name: The name of the validator.
            validator: The validator function.
        """
        self._validators[name] = validator
    
    def get(self, name: str) -> Optional[ValidatorFunc]:
        """Get a validator by name.
        
        Args:
            name: The name of the validator.
            
        Returns:
            The validator function, or None if not found.
        """
        return self._validators.get(name)
    
    def register_standard_validators(self) -> None:
        """Register standard validator functions."""
        # Register common validators
        self.register("min_length", min_length)
        self.register("max_length", max_length)
        self.register("pattern", pattern)
        self.register("min_value", min_value)
        self.register("max_value", max_value)


class ParameterTypeRegistry:
    """Registry for parameter types.
    
    This class maintains a collection of parameter types and their associated
    validation functions.
    """
    
    def __init__(self) -> None:
        """Initialize a new parameter type registry."""
        self._types: Dict[str, Tuple[str, TypeValidatorFunc]] = {}
    
    def register(self, type_name: str, description: str, validator: TypeValidatorFunc) -> None:
        """Register a parameter type.
        
        Args:
            type_name: The name of the parameter type.
            description: A description of the parameter type.
            validator: The validation function for this type.
        """
        self._types[type_name] = (description, validator)
    
    def get(self, type_name: str) -> Optional[Tuple[str, TypeValidatorFunc]]:
        """Get a parameter type by name.
        
        Args:
            type_name: The name of the parameter type.
            
        Returns:
            A tuple of (description, validator), or None if not found.
        """
        return self._types.get(type_name)
    
    def validate(self, type_name: str, value: str) -> Tuple[Any, Optional[str]]:
        """Validate a value against a parameter type.
        
        Args:
            type_name: The name of the parameter type.
            value: The value to validate.
            
        Returns:
            A tuple of (validated_value, error_message).
            If validation succeeds, error_message will be None.
        """
        type_info = self.get(type_name)
        if type_info is None:
            return None, f"Unknown parameter type: {type_name}"
        
        _, validator = type_info
        return validator(value)
    
    def register_standard_types(self) -> None:
        """Register standard parameter types."""
        # String type
        self.register(
            "string",
            "A text string",
            lambda value: (value, None)
        )
        
        # Integer type
        self.register(
            "integer",
            "A whole number",
            lambda value: _validate_integer(value)
        )
        
        # Float type
        self.register(
            "float",
            "A floating-point number",
            lambda value: _validate_float(value)
        )
        
        # Boolean type
        self.register(
            "boolean",
            "A boolean value (true/false)",
            lambda value: _validate_boolean(value)
        )
        
        # User ID type
        self.register(
            "user_id",
            "A Slack user ID",
            lambda value: _validate_user_id(value)
        )
        
        # Channel ID type
        self.register(
            "channel_id",
            "A Slack channel ID",
            lambda value: _validate_channel_id(value)
        )
        
        # Email type
        self.register(
            "email",
            "An email address",
            lambda value: _validate_email(value)
        )
        
        # URL type
        self.register(
            "url",
            "A URL",
            lambda value: _validate_url(value)
        )
        
        # Choice type - requires additional parameters
        self.register(
            "choice",
            "One of a predefined set of choices",
            lambda value, choices=None: _validate_choice(value, choices)
        )


# Create global instances of registries
validator_registry = ValidatorRegistry()
validator_registry.register_standard_validators()

param_type_registry = ParameterTypeRegistry()
param_type_registry.register_standard_types()


# For backward compatibility with existing code
class ParameterType(Enum):
    """Parameter types for validation.
    
    This enum provides backward compatibility with existing code.
    For new code, it's recommended to use strings with the parameter type registry.
    """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    USER_ID = "user_id"
    CHANNEL_ID = "channel_id"
    EMAIL = "email"
    DATE = "date"
    URL = "url"
    CHOICE = "choice"


@dataclass
class Parameter:
    """Parameter definition for command validation.
    
    This class defines a parameter expected by a command, including
    its name, type, and validation rules.
    
    Attributes:
        name: The name of the parameter.
        type: The type of the parameter (string or ParameterType enum).
        required: Whether the parameter is required.
        help_text: Help text describing the parameter.
        choices: Optional choices for CHOICE type parameters.
        default: Default value for the parameter if not provided.
        validators: Additional validation functions.
        type_kwargs: Additional keyword arguments for type validation.
    """
    name: str
    type: Union[str, ParameterType]
    required: bool = False
    help_text: Optional[str] = None
    choices: Optional[List[str]] = None
    default: Optional[Any] = None
    validators: List[Union[ValidatorFunc, Tuple[str, Any]]] = field(default_factory=list)
    type_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate parameter configuration after initialization."""
        # Convert ParameterType enum to string if needed
        if isinstance(self.type, ParameterType):
            self.type = self.type.value
        
        # Add choices to type_kwargs for CHOICE type
        if self.type == "choice" and self.choices:
            self.type_kwargs["choices"] = self.choices
        
        # Validate parameter configuration
        if self.type == "choice" and not self.choices and "choices" not in self.type_kwargs:
            raise ValueError("CHOICE parameter type requires choices to be specified")
        
        # Convert named validators to functions
        resolved_validators = []
        for validator in self.validators:
            if isinstance(validator, tuple) and len(validator) == 2:
                validator_name, validator_args = validator
                validator_func = validator_registry.get(validator_name)
                if validator_func:
                    if validator_args is None:
                        # If args is None, call the validator directly without arguments
                        resolved_validators.append(validator_func)
                    elif isinstance(validator_args, dict):
                        resolved_validators.append(partial(validator_func, **validator_args))
                    else:
                        resolved_validators.append(partial(validator_func, validator_args))
            else:
                resolved_validators.append(validator)
        
        self.validators = resolved_validators


class ValidationResult:
    """Result of parameter validation.
    
    Attributes:
        valid: Whether validation succeeded.
        errors: Dictionary of parameter names to error messages.
        validated_params: Dictionary of validated parameters with proper types.
    """
    
    def __init__(self) -> None:
        """Initialize a new validation result."""
        self.valid: bool = True
        self.errors: Dict[str, str] = {}
        self.validated_params: Dict[str, Any] = {}
    
    def add_error(self, param_name: str, error_msg: str) -> None:
        """Add a validation error.
        
        Args:
            param_name: The name of the parameter with the error.
            error_msg: The error message.
        """
        self.valid = False
        self.errors[param_name] = error_msg
    
    def add_param(self, param_name: str, value: Any) -> None:
        """Add a validated parameter.
        
        Args:
            param_name: The name of the parameter.
            value: The validated value.
        """
        self.validated_params[param_name] = value
    
    def as_command_response(self) -> CommandResponse:
        """Convert to a CommandResponse object.
        
        Returns:
            CommandResponse: A response indicating validation success or failure.
        """
        if self.valid:
            return CommandResponse("Validation passed", success=True)
        
        # Format error messages
        error_messages = []
        for param, error in self.errors.items():
            error_messages.append(f"{param}: {error}")
        
        return CommandResponse.error(
            f"Invalid parameters:\n" + "\n".join(error_messages)
        )


def validate_params(
    parameters: List[Parameter], 
    tokens: List[str],
    named_params: Optional[Dict[str, str]] = None
) -> ValidationResult:
    """Validate command parameters against provided tokens and named parameters.
    
    Args:
        parameters: List of parameter definitions to validate against.
        tokens: List of command tokens (positional parameters).
        named_params: Dictionary of named parameters (from Slack).
        
    Returns:
        ValidationResult: Result of the validation.
    """
    result = ValidationResult()
    
    # Initialize with named parameters if provided
    params_dict = {}
    if named_params:
        params_dict = named_params.copy()
    
    # Process positional parameters (tokens)
    for i, token in enumerate(tokens):
        if i < len(parameters):
            param = parameters[i]
            params_dict[param.name] = token
    
    # Track parameters that have been processed
    processed_params: Set[str] = set()
    
    # Validate each parameter
    for param in parameters:
        # Check if parameter is provided
        if param.name in params_dict:
            value = params_dict[param.name]
            processed_params.add(param.name)
            
            # Validate the parameter value
            validated_value, error = _validate_parameter_value(param, value)
            
            if error:
                result.add_error(param.name, error)
            else:
                result.add_param(param.name, validated_value)
        elif param.required:
            # Parameter is required but not provided
            result.add_error(param.name, "Required parameter missing")
        elif param.default is not None:
            # Use default value
            result.add_param(param.name, param.default)
    
    # Check for extra parameters that weren't defined
    extra_params = set(params_dict.keys()) - processed_params
    if extra_params:
        # Not adding these as errors, but we could if needed
        for param_name in extra_params:
            result.add_param(param_name, params_dict[param_name])
    
    return result


def _validate_parameter_value(param: Parameter, value: str) -> tuple[Any, Optional[str]]:
    """Validate a parameter value according to its type.
    
    Args:
        param: The parameter definition to validate against.
        value: The string value to validate.
        
    Returns:
        tuple: (validated_value, error_message)
        If validation succeeds, error_message will be None.
    """
    # Null check
    if value is None or value.strip() == "":
        if param.required:
            return None, "Value cannot be empty"
        return param.default, None
    
    # Get the parameter type as a string
    param_type = param.type
    
    # Validate the parameter using the type registry
    try:
        # Pass additional type kwargs if needed (e.g., choices for CHOICE type)
        if param.type_kwargs:
            validator_func = param_type_registry.get(param_type)[1]
            validated_value, error = validator_func(value, **param.type_kwargs)
        else:
            validated_value, error = param_type_registry.validate(param_type, value)
        
        # If validation failed, return the error
        if error:
            return None, error
        
        # Run additional validators if no error so far
        if validated_value is not None:
            for validator in param.validators:
                validator_error = validator(value)
                if validator_error:
                    return None, validator_error
        
        return validated_value, None
        
    except Exception as e:
        # Handle any unexpected errors
        return None, f"Validation error: {str(e)}"


# Helper functions for creating and registering custom parameter types
def register_parameter_type(
    type_name: str,
    description: str,
    validator: TypeValidatorFunc
) -> None:
    """Register a new parameter type.
    
    Args:
        type_name: The name of the parameter type.
        description: A description of the parameter type.
        validator: The validation function for this type.
    """
    param_type_registry.register(type_name, description, validator)


def register_validator(
    name: str,
    validator: ValidatorFunc
) -> None:
    """Register a new validator function.
    
    Args:
        name: The name of the validator.
        validator: The validator function.
    """
    validator_registry.register(name, validator)


# Example of registering a custom parameter type
def register_phone_number_type():
    """Register a phone number parameter type."""
    def validate_phone(value: str) -> Tuple[Optional[str], Optional[str]]:
        # Simple phone validation - adjust regex as needed
        phone_regex = r"^\+?[0-9]{10,15}$"
        if not re.match(phone_regex, value):
            return None, f"Invalid phone number: {value}. Expected format: +1234567890"
        return value, None
    
    register_parameter_type(
        "phone_number",
        "A phone number (10-15 digits, optionally starting with +)",
        validate_phone
    )


# Example of registering a custom validator
def register_allowed_domains_validator():
    """Register a validator for allowed email domains."""
    def allowed_domains(domains: List[str]) -> ValidatorFunc:
        def validator(value: str) -> Optional[str]:
            try:
                domain = value.split("@")[1]
                if domain not in domains:
                    return f"Email domain not allowed. Allowed domains: {', '.join(domains)}"
                return None
            except IndexError:
                return "Invalid email format"
        return validator
    
    register_validator("allowed_domains", allowed_domains) 