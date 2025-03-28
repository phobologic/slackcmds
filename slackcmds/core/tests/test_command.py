"""Tests for the Command class."""

import pytest
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse


class SampleCommand(Command):
    """Test command implementation."""
    
    def _execute_impl(self, context):
        return CommandResponse("Test command executed")


class SampleSubCommand(Command):
    """Test subcommand implementation."""
    
    def _execute_impl(self, context):
        return CommandResponse("Test subcommand executed")


def test_command_init():
    """Test Command initialization."""
    cmd = Command()
    assert cmd.name is None
    assert cmd.subcommands == {}
    assert cmd.short_help is None
    assert cmd.long_help is None


def test_command_set_name():
    """Test setting a command name."""
    cmd = Command()
    result = cmd._set_name("test")
    
    assert cmd.name == "test"
    assert result is cmd  # Method should return self for chaining


def test_command_set_help():
    """Test setting custom help text."""
    cmd = Command()
    result = cmd.set_help("Short help", "Long help text")
    
    assert cmd.short_help == "Short help"
    assert cmd.long_help == "Long help text"
    assert result is cmd  # Method should return self for chaining


def test_command_register_subcommand():
    """Test registering a subcommand."""
    cmd = Command()
    cmd._set_name("parent")
    subcmd = SampleSubCommand()
    
    result = cmd.register_subcommand("sub", subcmd)
    
    assert "sub" in cmd.subcommands
    assert cmd.subcommands["sub"] is subcmd
    assert subcmd.name == "parent sub"
    assert result is subcmd  # Method should return the subcommand instance


def test_command_execute_implementation():
    """Test executing a command with an implementation."""
    cmd = SampleCommand()
    cmd._set_name("test")
    
    result = cmd.execute()
    
    assert isinstance(result, CommandResponse)
    assert result.content == "Test command executed"
    assert result.success is True


def test_command_execute_no_implementation():
    """Test executing a command without an implementation."""
    cmd = Command()
    cmd._set_name("test")
    
    result = cmd.execute()
    
    assert isinstance(result, CommandResponse)
    assert "doesn't have an implementation" in result.content
    assert result.success is False


def test_command_validate():
    """Test command validation."""
    cmd = Command()
    
    result = cmd.validate()
    
    assert isinstance(result, CommandResponse)
    assert result.success is True


def test_command_show_help():
    """Test showing command help."""
    cmd = Command()
    cmd._set_name("test")
    
    subcmd1 = SampleCommand().set_help("Command 1 help")
    subcmd2 = SampleSubCommand()  # Uses docstring
    
    cmd.register_subcommand("cmd1", subcmd1)
    cmd.register_subcommand("cmd2", subcmd2)
    
    result = cmd.show_help()
    
    assert isinstance(result, CommandResponse)
    assert "Help: test" in result.content
    assert "Available Subcommands" in result.content
    assert "cmd1" in result.content
    assert "Command 1 help" in result.content
    assert "cmd2" in result.content
    assert "Test subcommand implementation" in result.content


def test_command_help_detection():
    """Test that help tokens are properly detected and handled."""
    cmd = Command()
    cmd._set_name("test")
    
    # Add a subcommand
    subcmd = SampleSubCommand()
    cmd.register_subcommand("sub", subcmd)
    
    # Test help for main command
    result = cmd.execute({"tokens": ["help"]})
    
    assert isinstance(result, CommandResponse)
    assert "Help: test" in result.content
    
    # Test help for specific subcommand
    result = cmd.execute({"tokens": ["help", "sub"]})
    
    assert isinstance(result, CommandResponse)
    assert "Help: test sub" in result.content


def test_has_custom_execution():
    """Test that _has_custom_execution correctly identifies custom implementations."""
    # Command with no custom implementation
    cmd = Command()
    assert cmd._has_custom_execution() is False
    
    # Command with custom implementation
    cmd = SampleCommand()
    assert cmd._has_custom_execution() is True


def test_show_invalid_subcommand_error():
    """Test that show_invalid_subcommand_error generates proper error messages."""
    # Setup a command with subcommands
    cmd = Command()
    cmd._set_name("test")
    
    subcmd1 = SampleCommand().set_help("Command 1 help")
    subcmd2 = SampleSubCommand()  # Uses docstring
    
    cmd.register_subcommand("cmd1", subcmd1)
    cmd.register_subcommand("cmd2", subcmd2)
    
    # Test error message
    result = cmd.show_invalid_subcommand_error("invalid")
    
    assert isinstance(result, CommandResponse)
    assert result.success is False
    assert "Error: 'invalid' is not a valid subcommand for 'test'" in result.content
    assert "Help: test" in result.content
    assert "Available Subcommands" in result.content
    assert "cmd1" in result.content
    assert "cmd2" in result.content
    
    # Test with Block Kit formatting
    cmd.use_block_kit = True
    result = cmd.show_invalid_subcommand_error("invalid")
    
    assert isinstance(result, CommandResponse)
    assert result.success is False
    
    # Block Kit response should have content as a list of blocks
    assert isinstance(result.content, list)
    
    # Check first block has error message
    assert "Error: 'invalid' is not a valid subcommand for 'test'" in result.content[0]["text"]["text"]


def test_invalid_subcommand_detection():
    """Test that invalid subcommands are detected and show appropriate error."""
    # Setup a command with subcommands
    cmd = Command()
    cmd._set_name("parent")
    
    subcmd1 = SampleCommand()
    subcmd2 = SampleSubCommand()
    
    cmd.register_subcommand("valid1", subcmd1)
    cmd.register_subcommand("valid2", subcmd2)
    
    # Test with an invalid subcommand
    result = cmd.execute({"tokens": ["invalid"]})
    
    assert isinstance(result, CommandResponse)
    assert result.success is False
    assert "Error: 'invalid' is not a valid subcommand for 'parent'" in result.content
    
    # Test with a command that has custom implementation and subcommands
    class CustomParentCommand(Command):
        """Custom parent command with implementation."""
        
        def __init__(self):
            super().__init__()
            self.register_subcommand("sub", SampleSubCommand())
            # Explicitly set to True to indicate this command can handle any tokens
            self.accepts_arguments = True
        
        def _execute_impl(self, context):
            if "tokens" in context and context["tokens"]:
                # Parent command with tokens should handle them itself
                return CommandResponse(f"Parent handled: {context['tokens'][0]}")
            return CommandResponse("Parent executed")
    
    parent_cmd = CustomParentCommand()
    parent_cmd._set_name("custom")
    
    # Test with an "invalid" token that should be handled by the parent
    result = parent_cmd.execute({"tokens": ["something"]})
    
    # This should NOT trigger invalid subcommand error because the parent
    # accepts arguments
    assert isinstance(result, CommandResponse)
    assert result.success is True
    assert result.content == "Parent handled: something"


def test_command_with_registry_integration():
    """Test that commands and registry work together to handle subcommands."""
    # Import registry here to avoid circular imports in the module
    from slackcmds.core.registry import CommandRegistry
    
    # Create a registry
    registry = CommandRegistry()
    
    # Create and register a top-level command with subcommands
    class WeatherCommand(Command):
        """Get weather information."""
        
        def __init__(self):
            super().__init__()
            self.register_subcommand("today", TodayCommand())
            self.register_subcommand("forecast", ForecastCommand())
            # Command with subcommands doesn't accept arbitrary arguments
            self.accepts_arguments = False
        
        def _execute_impl(self, context):
            # The base class now handles invalid subcommands automatically
            return self.show_help()
    
    class TodayCommand(Command):
        """Get today's weather."""
        
        def _execute_impl(self, context):
            return CommandResponse("Today's weather: Sunny and 75°F")
    
    class ForecastCommand(Command):
        """Get weather forecast."""
        
        def _execute_impl(self, context):
            return CommandResponse("Weather forecast for the week")
    
    # Register the command
    registry.register_command("weather", WeatherCommand())
    
    # Test with a valid subcommand
    result = registry.route_command("weather today")
    
    assert isinstance(result, CommandResponse)
    assert result.success is True
    assert result.content == "Today's weather: Sunny and 75°F"
    
    # Test with an invalid subcommand
    result = registry.route_command("weather invalid")
    
    assert isinstance(result, CommandResponse)
    assert result.success is False
    assert "Error: 'invalid' is not a valid subcommand for 'weather'" in result.content
    
    # Test without a subcommand (should show help)
    result = registry.route_command("weather")
    
    assert isinstance(result, CommandResponse)
    assert "Help: weather" in result.content
    assert "Available Subcommands" in result.content
    assert "today" in result.content
    assert "forecast" in result.content
