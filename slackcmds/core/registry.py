"""
Command registry implementation.

This module provides the CommandRegistry class for registering and
routing commands and subcommands.
"""

import logging
from typing import Dict, List, Optional, Any, TypeVar, cast

from .command import Command
from .response import CommandResponse

logger = logging.getLogger("slackcmds.registry")


class CommandRegistry:
    """Registry for top-level commands.
    
    This class provides methods for registering commands and routing
    command strings to the appropriate handlers.
    
    Attributes:
        top_level_commands: Dictionary of registered top-level commands.
    """
    
    def __init__(self) -> None:
        """Initialize a new command registry."""
        self.top_level_commands: Dict[str, Command] = {}
    
    def register_command(self, name: str, command_instance: Command) -> Command:
        """Register a top-level command.
        
        Args:
            name: Name of the command.
            command_instance: Instance of Command class to handle the command.
            
        Returns:
            The registered command instance for method chaining.
        """
        command_instance._set_name(name)
        self.top_level_commands[name] = command_instance
        logger.info(f"Registered top-level command: {name}")
        return command_instance
    
    def route_command(self, command_string: str, context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """Route a command string to the appropriate handler.
        
        Args:
            command_string: The full command string to route.
            context: The execution context to pass to the command.
            
        Returns:
            CommandResponse: Response from the executed command.
        """
        if context is None:
            context = {}
        
        # Handle empty command
        if not command_string or command_string.isspace():
            return self._show_top_level_help()
        
        # Split command into parts
        parts = command_string.strip().split()
        cmd_name = parts[0].lower()
        
        # Check if this is a top-level command
        if cmd_name not in self.top_level_commands:
            return CommandResponse.error(
                f"Unknown command: {cmd_name}. Type 'help' to see available commands."
            )
        
        # Get the command
        command = self.top_level_commands[cmd_name]
        
        # Handle subcommands
        if len(parts) > 1:
            return self._route_subcommand(command, parts[1:], context)
        
        # Execute the top-level command
        return command.execute(context)
    
    def _route_subcommand(self, parent_command: Command, subcommand_parts: List[str], 
                         context: Dict[str, Any]) -> CommandResponse:
        """Route to a subcommand of the given parent command.
        
        Args:
            parent_command: The parent command.
            subcommand_parts: The parts of the subcommand string.
            context: The execution context.
            
        Returns:
            CommandResponse: Response from the executed command.
        """
        subcmd_name = subcommand_parts[0].lower()
        
        # Check for help command
        if subcmd_name == "help":
            if len(subcommand_parts) > 1:
                # Help for a specific subcommand
                specific_subcmd = subcommand_parts[1].lower()
                if specific_subcmd in parent_command.subcommands:
                    return parent_command.subcommands[specific_subcmd].show_help()
            
            # General help for the parent command
            return parent_command.show_help()
        
        # Check if subcommand exists
        if subcmd_name not in parent_command.subcommands:
            return CommandResponse.error(
                f"Unknown subcommand: {subcmd_name}. Type '{parent_command.name} help' for available subcommands."
            )
        
        # Get the subcommand
        subcommand = parent_command.subcommands[subcmd_name]
        
        # Update context with subcommand info
        context['subcommand'] = subcmd_name
        
        # If there are more parts, route to sub-subcommand
        if len(subcommand_parts) > 1:
            return self._route_subcommand(subcommand, subcommand_parts[1:], context)
        
        # Execute the subcommand
        return subcommand.execute(context)
    
    def _show_top_level_help(self) -> CommandResponse:
        """Show help for all top level commands.
        
        Returns:
            CommandResponse: A formatted help response listing all commands.
        """
        help_text = "*Available Commands:*\n"
        
        for cmd_name, cmd in self.top_level_commands.items():
            # Get short description
            short_desc = cmd.short_help
            if not short_desc and cmd.__doc__:
                short_desc = cmd.__doc__.strip().split('\n')[0]
            
            help_text += f"• `{cmd_name}`: {short_desc}\n"
        
        help_text += "\nType `<command> help` for more details on a specific command."
        return CommandResponse(help_text)
