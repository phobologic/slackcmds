"""Tests for the CommandRegistry class."""

import pytest
import logging
import os

# Configure logging for tests
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)',
    datefmt='%Y-%m-%d %H:%M:%S',
)

from slackcmds.core.registry import CommandRegistry
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse

logger = logging.getLogger("slackcmds.tests")


class SampleCommand(Command):
    """Test command with subcommands."""
    
    def _execute_impl(self, context):
        return CommandResponse("Main command executed")


class SampleSubCommand(Command):
    """Test subcommand that captures arguments."""
    
    def _execute_impl(self, context):
        import logging
        logger = logging.getLogger("slackcmds.test")
        logger.debug(f"SampleSubCommand._execute_impl called with context: {context}")
        tokens = context.get("tokens", [])
        logger.debug(f"Tokens in SampleSubCommand: {tokens}")
        
        logger.debug(f"SampleSubCommand executing with tokens: {tokens}")
        return CommandResponse(f"Executed subcommand with args: {tokens}")


class SampleTopCommand(Command):
    """Test top-level command."""
    
    def _execute_impl(self, context):
        # Check if we have tokens that might be unknown subcommands
        if context and context.get("tokens"):
            tokens = context["tokens"]
            # Handle unknown subcommand
            if tokens[0].lower() not in self.subcommands:
                return CommandResponse.error(
                    f"Unknown subcommand: {tokens[0]}. Type '{self.name} help' for available subcommands."
                )
        
        return CommandResponse("Top-level executed")


class SampleSubCommandSimple(Command):
    """Test simple subcommand."""
    
    def _execute_impl(self, context):
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
    subcmd = SampleSubCommandSimple()
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


def test_subcommand_with_help_argument():
    """Test that 'command subcommand help' shows help for the subcommand."""
    logger.info("Starting test_subcommand_with_help_argument")
    
    # Create a registry
    registry = CommandRegistry()
    
    # Create a test command with a subcommand
    cmd = SampleCommand()
    subcmd = SampleSubCommand()
    cmd.register_subcommand("echo", subcmd)
    
    # Register the command
    registry.register_command("test", cmd)
    
    logger.debug("About to route command 'test echo help'")
    
    # Route the command with help as an argument
    response = registry.route_command("test echo help")
    
    logger.debug(f"Response content: {response.content}")
    
    # Verify this shows help, not execution
    assert response.success is True
    assert "Help:" in response.content
    assert "echo" in response.content
    # This would be in the response if the command was executed rather than showing help
    assert "Executed subcommand with args: ['help']" not in response.content
    
    logger.info("Completed test_subcommand_with_help_argument")
