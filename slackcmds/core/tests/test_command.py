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
