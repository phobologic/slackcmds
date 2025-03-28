"""
Test fixtures for the Slack Command Library.

This module provides reusable test fixtures that can be used by 
any test module in the project.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from slack_bolt import App

from slackcmds.core.command import Command
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.response import CommandResponse


class TestCommand(Command):
    """Test command that returns a simple success response."""
    
    def _execute_impl(self, context):
        return CommandResponse.success("Test command executed")


class TestSubCommand(Command):
    """Test subcommand that incorporates some context info."""
    
    def _execute_impl(self, context):
        user_id = context.get("user_id", "unknown") if context else "unknown"
        return CommandResponse.success(f"Hello, <@{user_id}>!")


class TestParamCommand(Command):
    """Test command with parameters."""
    
    def __init__(self):
        super().__init__()
        from slackcmds.core.validation import Parameter, min_length
        
        self.add_parameters([
            Parameter("name", "string", required=True, 
                      validators=[min_length(3)],
                      help_text="Name (min 3 characters)"),
            Parameter("value", "integer", required=False,
                      default=42,
                      help_text="A numeric value (default: 42)")
        ])
    
    def _execute_impl(self, context):
        params = context["validated_params"]
        name = params["name"]
        value = params["value"]
        return CommandResponse.success(f"Received {name} with value {value}")


@pytest.fixture
def command():
    """Create a basic test command."""
    cmd = TestCommand()
    cmd._set_name("test")
    return cmd


@pytest.fixture
def subcommand():
    """Create a test subcommand."""
    cmd = TestSubCommand()
    cmd._set_name("sub")
    return cmd


@pytest.fixture
def param_command():
    """Create a test command with parameters."""
    cmd = TestParamCommand()
    cmd._set_name("param")
    return cmd


@pytest.fixture
def registry():
    """Create a test registry with basic commands."""
    reg = CommandRegistry()
    
    # Add test command
    cmd = TestCommand()
    reg.register_command("test", cmd)
    
    # Add a subcommand
    subcmd = TestSubCommand()
    cmd.register_subcommand("sub", subcmd)
    
    # Add a command with parameters
    param_cmd = TestParamCommand()
    reg.register_command("param", param_cmd)
    
    return reg


@pytest.fixture
def mock_context():
    """Create a mock context object for command execution."""
    return {
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
        "tokens": []
    }


@pytest.fixture
def mock_slack_command():
    """Create a mock Slack command payload."""
    return {
        "command": "/test",
        "text": "test",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
        "api_app_id": "A111222333",
        "response_url": "https://hooks.slack.com/commands/T11223344/12345/abcde",
        "trigger_id": "111.222.abcde"
    }


@pytest.fixture
def mock_slack_app():
    """Create a mock Slack Bolt app."""
    app = MagicMock(spec=App)
    
    # Mock the command handler registration
    app.command = MagicMock(return_value=lambda func: func)
    
    return app


@pytest.fixture
def mock_say():
    """Create a mock say function."""
    return MagicMock()


@pytest.fixture
def mock_ack():
    """Create a mock ack function."""
    return MagicMock() 