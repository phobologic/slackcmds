"""
Tests for the Help System.

This module contains tests for the help text generation functionality, 
including docstring extraction, command listings, and Block Kit formatting.
"""

import pytest
from slackcmds.core.command import Command
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.response import CommandResponse


class SampleCommand(Command):
    """A sample command for testing.
    
    This is a longer description that spans
    multiple lines for testing purposes.
    """
    
    def execute(self, context=None):
        return CommandResponse("Sample command executed")


class SampleSubCommand(Command):
    """A sample subcommand for testing."""
    
    def execute(self, context=None):
        return CommandResponse("Sample subcommand executed")


def test_text_help_generation():
    """Test basic text-based help generation."""
    # Create a command
    cmd = SampleCommand()
    cmd._set_name("sample")
    
    # Get help response
    response = cmd.show_help()
    
    # Check response
    assert response.success is True
    assert "Help: sample" in response.content
    assert "A sample command for testing" in response.content
    assert "This is a longer description" in response.content


def test_help_with_subcommands():
    """Test help generation for commands with subcommands."""
    # Create a command with subcommands
    cmd = SampleCommand()
    cmd._set_name("sample")
    
    # Add subcommands
    subcmd = SampleSubCommand()
    cmd.register_subcommand("sub", subcmd)
    
    # Get help response
    response = cmd.show_help()
    
    # Check response
    assert response.success is True
    assert "Available Subcommands:" in response.content
    assert "sub" in response.content
    assert "A sample subcommand for testing" in response.content
    assert "sample help <subcommand>" in response.content


def test_override_help_text():
    """Test overriding the default help text."""
    # Create a command
    cmd = SampleCommand()
    cmd._set_name("sample")
    
    # Override help text
    cmd.set_help(
        short_help="Custom short help",
        long_help="Custom long help text",
        usage_example="sample [options]"
    )
    
    # Get help response
    response = cmd.show_help()
    
    # Check response
    assert response.success is True
    assert "Help: sample" in response.content
    assert "Custom long help text" in response.content
    assert "Usage:" in response.content
    assert "sample [options]" in response.content


def test_block_kit_help_generation():
    """Test Block Kit formatted help generation."""
    # Create a command
    cmd = SampleCommand()
    cmd._set_name("sample")
    
    # Set to use Block Kit
    cmd.set_help(use_block_kit=True)
    
    # Get help response
    response = cmd.show_help()
    
    # Check response
    assert response.success is True
    
    # Should be a list of block objects
    assert isinstance(response.content, list)
    
    # Find header block
    header_block = next((b for b in response.content if b["type"] == "header"), None)
    assert header_block is not None
    assert header_block["text"]["text"] == "Help: sample"
    
    # Find section with description
    description_block = next((b for b in response.content if b["type"] == "section" and "A sample command for testing" in b["text"]["text"]), None)
    assert description_block is not None


def test_block_kit_help_with_usage():
    """Test Block Kit help with usage example."""
    # Create a command
    cmd = SampleCommand()
    cmd._set_name("sample")
    
    # Set usage example and Block Kit format
    cmd.set_help(usage_example="sample [options]", use_block_kit=True)
    
    # Get help response
    response = cmd.show_help()
    
    # Check response
    assert response.success is True
    
    # Find usage section
    usage_block = next((b for b in response.content if b["type"] == "section" and "Usage:" in b["text"]["text"]), None)
    assert usage_block is not None
    assert "sample [options]" in usage_block["text"]["text"]


def test_registry_top_level_help():
    """Test top-level help from the registry."""
    # Create registry
    registry = CommandRegistry()
    
    # Register commands
    cmd1 = SampleCommand()
    registry.register_command("cmd1", cmd1)
    
    cmd2 = SampleCommand()
    cmd2.set_help(short_help="Custom help for cmd2")
    registry.register_command("cmd2", cmd2)
    
    # Get help response
    response = registry.route_command("help", {})
    
    # Check response
    assert response.success is True
    assert "Available Commands:" in response.content
    assert "cmd1" in response.content
    assert "cmd2" in response.content
    assert "Custom help for cmd2" in response.content


def test_registry_block_kit_help():
    """Test Block Kit formatted top-level help from the registry."""
    # Create registry with Block Kit format
    registry = CommandRegistry(help_format="block_kit")
    
    # Register commands
    cmd1 = SampleCommand()
    registry.register_command("cmd1", cmd1)
    
    cmd2 = SampleCommand()
    cmd2.set_help(short_help="Custom help for cmd2")
    registry.register_command("cmd2", cmd2)
    
    # Get help response
    response = registry.route_command("help", {})
    
    # Check response
    assert response.success is True
    
    # Should be a list of block objects
    assert isinstance(response.content, list)
    
    # Find header block
    header_block = next((b for b in response.content if b["type"] == "header"), None)
    assert header_block is not None
    assert header_block["text"]["text"] == "Available Commands"
    
    # Find commands list
    commands_block = next((b for b in response.content if b["type"] == "section" and "cmd1" in b["text"]["text"]), None)
    assert commands_block is not None
    assert "cmd2" in commands_block["text"]["text"]
    assert "Custom help for cmd2" in commands_block["text"]["text"] 