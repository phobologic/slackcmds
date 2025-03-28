"""Tests for the validation framework."""

import pytest
import re

from slackcmds.core.validation import (
    Parameter, ParameterType, ValidationResult,
    validate_params, min_length, max_length, pattern,
    min_value, max_value, register_parameter_type, register_validator,
    ValidatorFunc, TypeValidatorFunc
)


def test_validation_result():
    """Test ValidationResult class."""
    # Valid result
    result = ValidationResult()
    assert result.valid is True
    assert not result.errors
    assert not result.validated_params
    
    # Add a valid parameter
    result.add_param("name", "test")
    assert result.valid is True
    assert "name" in result.validated_params
    assert result.validated_params["name"] == "test"
    
    # Add an error
    result.add_error("age", "Must be a positive number")
    assert result.valid is False
    assert "age" in result.errors
    assert result.errors["age"] == "Must be a positive number"
    
    # Test as_command_response
    response = result.as_command_response()
    assert response.success is False
    assert "Invalid parameters" in response.content
    assert "age: Must be a positive number" in response.content


def test_validate_params_basic():
    """Test basic parameter validation."""
    # Define parameters
    parameters = [
        Parameter("name", "string", required=True),
        Parameter("age", "integer", required=False)
    ]
    
    # Test with valid input
    tokens = ["John", "30"]
    result = validate_params(parameters, tokens)
    assert result.valid is True
    assert result.validated_params["name"] == "John"
    assert result.validated_params["age"] == 30
    
    # Test with missing required parameter
    tokens = []
    result = validate_params(parameters, tokens)
    assert result.valid is False
    assert "name" in result.errors
    assert "Required parameter missing" in result.errors["name"]
    
    # Test with invalid type
    tokens = ["John", "not-a-number"]
    result = validate_params(parameters, tokens)
    assert result.valid is False
    assert "age" in result.errors
    assert "Invalid value for integer" in result.errors["age"]


def test_validate_params_with_named_params():
    """Test parameter validation with named parameters."""
    # Define parameters
    parameters = [
        Parameter("name", "string", required=True),
        Parameter("age", "integer", required=True)
    ]
    
    # Test with named parameters
    named_params = {"name": "John", "age": "30"}
    result = validate_params(parameters, [], named_params)
    assert result.valid is True
    assert result.validated_params["name"] == "John"
    assert result.validated_params["age"] == 30
    
    # Test with mix of positional and named parameters (named takes precedence)
    tokens = ["Bob"]
    named_params = {"age": "25"}
    result = validate_params(parameters, tokens, named_params)
    assert result.valid is True
    assert result.validated_params["name"] == "Bob"
    assert result.validated_params["age"] == 25


def test_parameter_types():
    """Test validation of different parameter types."""
    # Test STRING type
    param = Parameter("name", "string")
    result = validate_params([param], ["test"])
    assert result.valid is True
    assert result.validated_params["name"] == "test"
    
    # Test INTEGER type
    param = Parameter("count", "integer")
    result = validate_params([param], ["42"])
    assert result.valid is True
    assert result.validated_params["count"] == 42
    assert isinstance(result.validated_params["count"], int)
    
    # Test FLOAT type
    param = Parameter("price", "float")
    result = validate_params([param], ["3.14"])
    assert result.valid is True
    assert result.validated_params["price"] == 3.14
    assert isinstance(result.validated_params["price"], float)
    
    # Test BOOLEAN type
    param = Parameter("active", "boolean")
    
    # Various true values
    for true_val in ["yes", "true", "True", "1", "Y"]:
        result = validate_params([param], [true_val])
        assert result.valid is True
        assert result.validated_params["active"] is True
    
    # Various false values
    for false_val in ["no", "false", "False", "0", "N"]:
        result = validate_params([param], [false_val])
        assert result.valid is True
        assert result.validated_params["active"] is False
    
    # Invalid boolean
    result = validate_params([param], ["neither"])
    assert result.valid is False
    assert "Invalid boolean value" in result.errors["active"]
    
    # Test USER_ID type
    param = Parameter("user", "user_id")
    result = validate_params([param], ["U12345678"])
    assert result.valid is True
    assert result.validated_params["user"] == "U12345678"
    
    # With Slack formatting
    result = validate_params([param], ["<@U12345678>"])
    assert result.valid is True
    assert result.validated_params["user"] == "U12345678"
    
    # Invalid user ID
    result = validate_params([param], ["X12345678"])
    assert result.valid is False
    assert "Invalid user ID" in result.errors["user"]
    
    # Test EMAIL type
    param = Parameter("email", "email")
    
    # Standard email
    result = validate_params([param], ["user@example.com"])
    assert result.valid is True
    assert result.validated_params["email"] == "user@example.com"
    
    # Slack mailto format
    result = validate_params([param], ["<mailto:user@example.com|user@example.com>"])
    assert result.valid is True
    assert result.validated_params["email"] == "user@example.com"
    
    # Invalid email
    result = validate_params([param], ["not-an-email"])
    assert result.valid is False
    assert "Invalid email address" in result.errors["email"]
    
    # Test URL type
    param = Parameter("website", "url")
    
    # Standard URL
    result = validate_params([param], ["https://example.com"])
    assert result.valid is True
    assert result.validated_params["website"] == "https://example.com"
    
    # Slack URL format
    result = validate_params([param], ["<https://example.com|example.com>"])
    assert result.valid is True
    assert result.validated_params["website"] == "https://example.com"
    
    # Invalid URL
    result = validate_params([param], ["not-a-url"])
    assert result.valid is False
    assert "Invalid URL" in result.errors["website"]
    
    # Test CHOICE type
    param = Parameter("color", "choice", choices=["red", "green", "blue"])
    result = validate_params([param], ["red"])
    assert result.valid is True
    assert result.validated_params["color"] == "red"
    
    # Invalid choice
    result = validate_params([param], ["yellow"])
    assert result.valid is False
    assert "Invalid choice" in result.errors["color"]


def test_validators():
    """Test custom validator functions."""
    # Test min_length
    param = Parameter("password", "string", 
                     validators=[min_length(8)])
    result = validate_params([param], ["short"])
    assert result.valid is False
    assert "Value must be at least 8 characters long" in result.errors["password"]
    
    result = validate_params([param], ["longenough"])
    assert result.valid is True
    
    # Test max_length
    param = Parameter("username", "string", 
                     validators=[max_length(10)])
    result = validate_params([param], ["toolongusername"])
    assert result.valid is False
    assert "Value must be at most 10 characters long" in result.errors["username"]
    
    result = validate_params([param], ["shortname"])
    assert result.valid is True
    
    # Test pattern
    param = Parameter("code", "string", 
                     validators=[pattern(r'^[A-Z]{2}\d{4}$', "Code must be 2 uppercase letters followed by 4 digits")])
    result = validate_params([param], ["AB1234"])
    assert result.valid is True
    
    result = validate_params([param], ["AB123"])
    assert result.valid is False
    assert "Code must be 2 uppercase letters followed by 4 digits" in result.errors["code"]
    
    # Test min_value
    param = Parameter("age", "integer", 
                     validators=[min_value(18)])
    result = validate_params([param], ["21"])
    assert result.valid is True
    
    result = validate_params([param], ["16"])
    assert result.valid is False
    assert "Value must be at least 18" in result.errors["age"]
    
    # Test max_value
    param = Parameter("percentage", "float", 
                     validators=[max_value(100.0)])
    result = validate_params([param], ["75.5"])
    assert result.valid is True
    
    result = validate_params([param], ["120.0"])
    assert result.valid is False
    assert "Value must be at most 100.0" in result.errors["percentage"]


def test_default_values():
    """Test parameter default values."""
    # Define parameter with default
    param = Parameter("limit", "integer", default=10)
    result = validate_params([param], [])
    assert result.valid is True
    assert result.validated_params["limit"] == 10
    
    # Provided value should override default
    result = validate_params([param], ["20"])
    assert result.valid is True
    assert result.validated_params["limit"] == 20


def test_multiple_parameters():
    """Test validating multiple parameters together."""
    parameters = [
        Parameter("name", "string", required=True),
        Parameter("age", "integer", required=True, validators=[min_value(0)]),
        Parameter("email", "email", required=False),
        Parameter("role", "choice", choices=["admin", "user", "guest"], default="user")
    ]
    
    # Test with all parameters valid
    tokens = ["John", "30", "john@example.com", "admin"]
    result = validate_params(parameters, tokens)
    assert result.valid is True
    assert result.validated_params["name"] == "John"
    assert result.validated_params["age"] == 30
    assert result.validated_params["email"] == "john@example.com"
    assert result.validated_params["role"] == "admin"
    
    # Test with some invalid parameters
    tokens = ["John", "-5", "not-an-email", "superuser"]
    result = validate_params(parameters, tokens)
    assert result.valid is False
    assert "age" in result.errors  # Negative age
    assert "email" in result.errors  # Invalid email
    assert "role" in result.errors  # Invalid role
    assert result.validated_params["name"] == "John"  # This one is valid


def test_parameter_enum_to_string_conversion():
    """Test conversion from ParameterType enum to string."""
    # Using enum
    param1 = Parameter("name", ParameterType.STRING, required=True)
    # Using string
    param2 = Parameter("name", "string", required=True)
    
    # Both should validate the same way
    result1 = validate_params([param1], ["test"])
    result2 = validate_params([param2], ["test"])
    
    assert result1.valid is True
    assert result2.valid is True
    assert result1.validated_params["name"] == result2.validated_params["name"]


def test_register_custom_parameter_type():
    """Test registering and using a custom parameter type."""
    # Define and register a custom parameter type
    def validate_zipcode(value: str):
        """Validate a US zipcode."""
        if re.match(r'^\d{5}(-\d{4})?$', value):
            return value, None
        return None, f"Invalid zipcode: {value}. Expected format: 12345 or 12345-6789"
    
    # Register it
    register_parameter_type("zipcode", "A US zipcode", validate_zipcode)
    
    # Use it
    param = Parameter("zip", "zipcode", required=True)
    
    # Test with valid zipcode
    result = validate_params([param], ["12345"])
    assert result.valid is True
    assert result.validated_params["zip"] == "12345"
    
    # Test with valid zipcode+4
    result = validate_params([param], ["12345-6789"])
    assert result.valid is True
    assert result.validated_params["zip"] == "12345-6789"
    
    # Test with invalid zipcode
    result = validate_params([param], ["1234"])
    assert result.valid is False
    assert "Invalid zipcode" in result.errors["zip"]


def test_register_custom_validator():
    """Test registering and using a custom validator."""
    # Define and register a custom validator
    def even_number(value: str):
        """Validate that a number is even."""
        try:
            num = int(value)
            if num % 2 != 0:
                return "Value must be an even number"
        except ValueError:
            return "Value must be a number"
        return None
    
    # Register it
    register_validator("even_number", even_number)
    
    # Use it
    param = Parameter("value", "integer", validators=[("even_number", None)])
    
    # Test with valid even number
    result = validate_params([param], ["42"])
    assert result.valid is True
    assert result.validated_params["value"] == 42
    
    # Test with invalid odd number
    result = validate_params([param], ["43"])
    assert result.valid is False
    assert "Value must be an even number" in result.errors["value"]
    
    # Test with non-number
    result = validate_params([param], ["not-a-number"])
    assert result.valid is False 