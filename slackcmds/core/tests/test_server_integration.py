"""
Tests for Server Integration with Slack Bolt.

This module contains tests for the server integration with Slack Bolt,
including command handling, context creation, and response formatting.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from slack_bolt import App

from slackcmds.core.command import Command
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.response import CommandResponse


class SampleCommand(Command):
    """Test command for server integration tests."""
    
    def _execute_impl(self, context):
        return CommandResponse.success("Test command executed successfully")


class SampleSubCommand(Command):
    """Test subcommand for server integration tests."""
    
    def _execute_impl(self, context):
        # Access user_id from context to test context passing
        user_id = context.get("user_id", "unknown") if context else "unknown"
        return CommandResponse.success(f"Hello, <@{user_id}>!")


@pytest.fixture
def registry():
    """Create a test registry with commands."""
    registry = CommandRegistry()
    
    # Add test commands
    cmd = SampleCommand()
    registry.register_command("test", cmd)
    
    # Add subcommand
    sub_cmd = SampleSubCommand()
    cmd.register_subcommand("greet", sub_cmd)
    
    return registry


@pytest.fixture
def mock_slack_app():
    """Create a mock Slack Bolt app."""
    app = MagicMock(spec=App)
    
    # Mock the command handler registration
    app.command = MagicMock(return_value=lambda func: func)
    
    return app


def test_slack_command_handler(registry, mock_slack_app):
    """Test the Slack command handler function."""
    # Create mock functions for slack_bolt
    mock_ack = MagicMock()
    mock_say = MagicMock()
    
    # Create mock command data
    command = {
        "command": "/test",
        "text": "test",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Define a command handler function similar to what would be in server.py
    def handle_command(ack, command, say):
        ack()  # Acknowledge receipt of the command
        
        # Create context object
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        # Route the command
        result = registry.route_command(command["text"], context)
        
        # Send the response
        say(**result.as_dict())
    
    # Call the handler with our mocks
    handle_command(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with the expected arguments
    expected_response = CommandResponse.success("Test command executed successfully").as_dict()
    mock_say.assert_called_once_with(**expected_response)


def test_slack_subcommand_handler(registry, mock_slack_app):
    """Test the Slack handler with a subcommand."""
    # Create mock functions for slack_bolt
    mock_ack = MagicMock()
    mock_say = MagicMock()
    
    # Create mock command data
    command = {
        "command": "/test",
        "text": "test greet",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Define a command handler function
    def handle_command(ack, command, say):
        ack()  # Acknowledge receipt of the command
        
        # Create context object
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        # Route the command
        result = registry.route_command(command["text"], context)
        
        # Send the response
        say(**result.as_dict())
    
    # Call the handler with our mocks
    handle_command(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with the expected arguments
    expected_response = CommandResponse.success("Hello, <@U12345678>!").as_dict()
    mock_say.assert_called_once_with(**expected_response)


def test_error_handling(registry, mock_slack_app):
    """Test error handling in the Slack command handler."""
    # Create mock functions for slack_bolt
    mock_ack = MagicMock()
    mock_say = MagicMock()
    
    # Create mock command data with an unknown command
    command = {
        "command": "/test",
        "text": "unknown",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Define a command handler function
    def handle_command(ack, command, say):
        ack()  # Acknowledge receipt of the command
        
        # Create context object
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        # Route the command
        result = registry.route_command(command["text"], context)
        
        # Send the response
        say(**result.as_dict())
    
    # Call the handler with our mocks
    handle_command(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with an error response
    mock_say.assert_called_once()
    call_args = mock_say.call_args[1]
    assert "Error" in call_args["text"]
    assert "Unknown command" in call_args["text"]


@patch('os.environ.get')
def test_socket_mode_support(mock_environ_get, mock_slack_app):
    """Test Socket Mode support in server initialization."""
    # Mock environment variable returns
    mock_environ_get.side_effect = lambda key, default=None: {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        "SLACK_APP_TOKEN": "xapp-test-token",
        "PORT": "3000",
    }.get(key, default)
    
    # Define a simplified start_server function similar to what would be in server.py
    def start_server(app):
        # Check if we're using Socket Mode
        if os.environ.get("SLACK_APP_TOKEN"):
            # Would start Socket Mode handler
            return "socket_mode"
        else:
            # Would start HTTP server
            port = int(os.environ.get("PORT", 3000))
            return f"http_mode:{port}"
    
    # Call the function
    result = start_server(mock_slack_app)
    
    # Verify the result
    assert result == "socket_mode"
    
    # Verify the environment variables were accessed
    assert mock_environ_get.call_args_list[0][0][0] == "SLACK_APP_TOKEN"


@patch('os.environ.get')
def test_http_mode_support(mock_environ_get, mock_slack_app):
    """Test HTTP mode support in server initialization."""
    # Mock environment variable returns
    mock_environ_get.side_effect = lambda key, default=None: {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        # No SLACK_APP_TOKEN here
        "PORT": "3000",
    }.get(key, default)
    
    # Define a simplified start_server function
    def start_server(app):
        # Check if we're using Socket Mode
        if os.environ.get("SLACK_APP_TOKEN"):
            # Would start Socket Mode handler
            return "socket_mode"
        else:
            # Would start HTTP server
            port = int(os.environ.get("PORT", 3000))
            return f"http_mode:{port}"
    
    # Call the function
    result = start_server(mock_slack_app)
    
    # Verify the result
    assert result == "http_mode:3000"
    
    # Verify the environment variables were accessed
    assert mock_environ_get.call_args_list[0][0][0] == "SLACK_APP_TOKEN" 