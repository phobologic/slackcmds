"""Tests for the CommandRegistry class."""

import pytest
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse


class SampleTopCommand(Command):
    """Test top-level command."""
    
    def execute(self, context=None):
        return CommandResponse("Top-level executed")


class SampleSubCommand(Command):
    """Test subcommand."""
    
    def execute(self, context=None):
        return CommandResponse("Subcommand executed")


def test_registry_init():
    """Test CommandRegistry initialization."""
    registry = CommandRegistry()
    assert registry.top_level_commands == {}


def test_register_command():
    """Test registering a top-level command."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    
    result = registry.register_command("test", cmd)
    
    assert "test" in registry.top_level_commands
    assert registry.top_level_commands["test"] is cmd
    assert cmd.name == "test"
    assert result is cmd  # Method should return the command instance


def test_route_command_top_level():
    """Test routing to a top-level command."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    registry.register_command("test", cmd)
    
    result = registry.route_command("test")
    
    assert isinstance(result, CommandResponse)
    assert result.content == "Top-level executed"


def test_route_command_unknown():
    """Test routing to an unknown command."""
    registry = CommandRegistry()
    
    result = registry.route_command("unknown")
    
    assert isinstance(result, CommandResponse)
    assert "Unknown command" in result.content
    assert not result.success


def test_route_command_empty():
    """Test routing an empty command string."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    registry.register_command("test", cmd)
    
    result = registry.route_command("")
    
    assert isinstance(result, CommandResponse)
    assert "Available Commands" in result.content


def test_route_subcommand():
    """Test routing to a subcommand."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    subcmd = SampleSubCommand()
    cmd.register_subcommand("sub", subcmd)
    registry.register_command("test", cmd)
    
    result = registry.route_command("test sub")
    
    assert isinstance(result, CommandResponse)
    assert result.content == "Subcommand executed"


def test_route_unknown_subcommand():
    """Test routing to an unknown subcommand."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    registry.register_command("test", cmd)
    
    result = registry.route_command("test unknown")
    
    assert isinstance(result, CommandResponse)
    assert "Unknown subcommand" in result.content
    assert not result.success


def test_route_help_command():
    """Test routing to the help command."""
    registry = CommandRegistry()
    cmd = SampleTopCommand()
    registry.register_command("test", cmd)
    
    result = registry.route_command("test help")
    
    assert isinstance(result, CommandResponse)
    assert "Help: test" in result.content
