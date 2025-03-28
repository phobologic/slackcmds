"""
End-to-end tests for the Slack Command Library.

These tests verify the complete flow from receiving a Slack command
to returning a formatted response.
"""

import pytest
from unittest.mock import MagicMock, patch

from slackcmds.core.command import Command
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.response import CommandResponse
from slackcmds.core.validation import Parameter


class WeatherCommand(Command):
    """Get weather information."""
    
    def __init__(self):
        super().__init__()
        self.register_subcommand("today", TodayWeatherCommand())
        self.register_subcommand("forecast", ForecastWeatherCommand())
    
    def _execute_impl(self, context):
        return self.show_help()


class TodayWeatherCommand(Command):
    """Get today's weather for a location."""
    
    def __init__(self):
        super().__init__()
        self.add_parameter(
            Parameter("location", "string", required=True,
                     help_text="Location to get weather for")
        )
    
    def _execute_impl(self, context):
        location = context["validated_params"]["location"]
        return CommandResponse.success(f"Today's weather for {location}: Sunny and 75°F")


class ForecastWeatherCommand(Command):
    """Get the weather forecast for a location."""
    
    def __init__(self):
        super().__init__()
        self.add_parameter(
            Parameter("location", "string", required=True,
                     help_text="Location to get forecast for")
        )
        self.add_parameter(
            Parameter("days", "integer", required=False, default=3,
                     help_text="Number of days (default: 3)")
        )
    
    def _execute_impl(self, context):
        params = context["validated_params"]
        location = params["location"]
        days = params["days"]
        
        if days > 5:
            return CommandResponse.error("Cannot forecast more than 5 days")
        
        forecasts = [
            f"Day 1: Sunny and 75°F",
            f"Day 2: Partly cloudy and 72°F",
            f"Day 3: Rainy and 65°F",
            f"Day 4: Overcast and 68°F",
            f"Day 5: Sunny and 70°F"
        ]
        
        # Get the requested number of days
        forecast_days = forecasts[:days]
        result = f"Weather forecast for {location}:\n" + "\n".join(forecast_days)
        
        # Use Block Kit for the response
        from slackcmds.core import block_kit
        blocks = [
            block_kit.header(f"Weather Forecast: {location}"),
            block_kit.divider()
        ]
        
        for day in forecast_days:
            blocks.append(block_kit.section(day))
            
        return CommandResponse.with_blocks(blocks, ephemeral=False)


def create_command_handler(registry):
    """Create a command handler function similar to what would be in a real server."""
    def handle_command(ack, command, say):
        ack()  # Acknowledge receipt of the command
        
        # Extract command text
        text = command["text"].strip() if command.get("text") else ""
        
        # Create context object
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        # Route the command
        result = registry.route_command(text, context)
        
        # Send the response
        say(**result.as_dict())
    
    return handle_command


@pytest.fixture
def weather_registry():
    """Create a registry with weather commands."""
    registry = CommandRegistry()
    registry.register_command("weather", WeatherCommand())
    return registry


def test_command_with_no_args(weather_registry, mock_ack, mock_say):
    """Test executing a command with no arguments."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "weather",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with help text (since no subcommand was specified)
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should be an ephemeral message
    assert args.get("response_type") == "ephemeral"
    
    # Should include "Help: weather"
    if "text" in args:
        assert "Help: weather" in args["text"]
    elif "blocks" in args:
        # If using Block Kit format, check the first block
        blocks_text = " ".join(str(b) for b in args["blocks"])
        assert "weather" in blocks_text
        assert "Get weather information" in blocks_text


def test_subcommand_with_missing_param(weather_registry, mock_ack, mock_say):
    """Test executing a subcommand with a missing parameter."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "weather today",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with error message
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should be an ephemeral message
    assert args.get("response_type") == "ephemeral"
    
    # Should include error about missing parameter
    assert "Error" in args["text"]
    assert "location: Required parameter missing" in args["text"]


def test_subcommand_with_valid_param(weather_registry, mock_ack, mock_say):
    """Test executing a subcommand with a valid parameter."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "weather today Seattle",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with success message
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should be an ephemeral message
    assert args.get("response_type") == "ephemeral"
    
    # Should include success message with location
    assert "Today's weather for Seattle" in args["text"]


def test_subcommand_with_block_kit_response(weather_registry, mock_ack, mock_say):
    """Test executing a subcommand that returns a Block Kit response."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "weather forecast Seattle 2",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with Block Kit response
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should be an in_channel message
    assert args.get("response_type") == "in_channel"
    
    # Should have blocks
    assert "blocks" in args
    
    # Should have header with location
    header = next((b for b in args["blocks"] if b["type"] == "header"), None)
    assert header is not None
    assert "Seattle" in header["text"]["text"]
    
    # Should have correct number of section blocks (2 days)
    sections = [b for b in args["blocks"] if b["type"] == "section"]
    assert len(sections) == 2


def test_help_subcommand(weather_registry, mock_ack, mock_say):
    """Test accessing help for a subcommand."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "weather forecast help",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with help text
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should include help information about the forecast command
    if "text" in args:
        # Fix: Check for "Help:" and "forecast" instead of exact string
        assert "Help:" in args["text"]
        assert "forecast" in args["text"]
        assert "Get the weather forecast for a location" in args["text"]
    elif "blocks" in args:
        blocks_text = " ".join(str(b) for b in args["blocks"])
        assert "forecast" in blocks_text
        assert "location" in blocks_text
        assert "days" in blocks_text


def test_invalid_command(weather_registry, mock_ack, mock_say):
    """Test handling an invalid command."""
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "unknown",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with error message
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should include error about unknown command
    assert "Error" in args["text"]
    assert "Unknown command" in args["text"]


def test_error_handling_in_command(weather_registry, mock_ack, mock_say):
    """Test error handling when a command raises an exception."""
    # Create a command that raises an exception
    class ErrorCommand(Command):
        """A command that raises an exception."""
        
        def _execute_impl(self, context):
            raise ValueError("This is a test error")
    
    # Register the command
    weather_registry.register_command("error", ErrorCommand())
    
    # Create the command handler
    handler = create_command_handler(weather_registry)
    
    # Create a command payload
    command = {
        "command": "/demo",
        "text": "error",
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Execute the handler
    handler(mock_ack, command, mock_say)
    
    # Verify ack was called
    mock_ack.assert_called_once()
    
    # Verify say was called with error message
    mock_say.assert_called_once()
    args = mock_say.call_args[1]
    
    # Should include error about the exception
    # Fix: Check for "unexpected error" instead of "Error"
    assert "unexpected error" in args["text"].lower()
    assert "This is a test error" in args["text"] 