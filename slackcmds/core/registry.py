"""
Command registry implementation.

This module provides the CommandRegistry class for registering and
routing commands and subcommands.
"""

import logging
from typing import Dict, List, Optional, Any, TypeVar, cast, Union, Literal

from .command import Command
from .response import CommandResponse

logger = logging.getLogger("slackcmds.registry")


class CommandRegistry:
    """Registry for top-level commands.
    
    This class provides methods for registering commands and routing
    command strings to the appropriate handlers.
    
    Attributes:
        top_level_commands: Dictionary of registered top-level commands.
        help_format: Format for help text display ('text' or 'block_kit').
    """
    
    def __init__(self, help_format: Literal['text', 'block_kit'] = 'text') -> None:
        """Initialize a new command registry.
        
        Args:
            help_format: The format to use for help text display ('text' or 'block_kit').
        """
        self.top_level_commands: Dict[str, Command] = {}
        self.help_format = help_format
    
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
        
        # Handle empty parts list (shouldn't happen but just in case)
        if not parts:
            return self._show_top_level_help()
        
        cmd_name = parts[0].lower()
        logger.debug(f"Top-level command name: {cmd_name}")
        
        # Check if this is a help command
        if cmd_name == 'help':
            return self._show_top_level_help()
        
        # Check if this is a top-level command
        if cmd_name not in self.top_level_commands:
            return CommandResponse.error(
                f"Unknown command: {cmd_name}. Type 'help' to see available commands."
            )
        
        # Get the top-level command
        current_command = self.top_level_commands[cmd_name]
        remaining_parts = parts[1:]
        
        logger.debug(f"Found top-level command: {cmd_name}")
        logger.debug(f"Remaining parts: {remaining_parts}")
        
        # Special handling for "<command> help" pattern - check if the first remaining part is "help"
        if remaining_parts and remaining_parts[0].lower() == "help":
            logger.debug(f"Help command detected for {cmd_name}")
            return current_command.show_help()
        
        # Process subcommands recursively
        command_path = [cmd_name]
        current_command, remaining_parts = self._find_deepest_command(
            current_command, remaining_parts, command_path
        )
        
        # Add the remaining parts as tokens in the context
        context["tokens"] = remaining_parts
        logger.debug(f"Final command: {current_command.name}")
        logger.debug(f"Command arguments (tokens): {remaining_parts}")
        
        # Execute the command with the context
        return current_command.execute(context)
    
    def _find_deepest_command(self, 
                             current_command: Command, 
                             parts: List[str], 
                             command_path: List[str]) -> tuple[Command, List[str]]:
        """Find the deepest valid command and separate it from arguments.
        
        Args:
            current_command: The current command being examined.
            parts: The remaining parts of the command string.
            command_path: The path of commands traversed so far.
            
        Returns:
            tuple: (deepest_command, remaining_arguments)
        """
        # Iterative implementation using a while loop
        command = current_command
        remaining_parts = parts.copy()  # Work with a copy to avoid modifying the original
        
        logger.debug(f"_find_deepest_command starting with command: {command.name}, parts: {remaining_parts}, path so far: {command_path}")
        
        while remaining_parts:
            # Special handling for help - this should have highest priority
            if remaining_parts[0].lower() == "help":
                logger.debug(f"Found 'help' token after command {command.name}, returning for help processing")
                # Help is requested for the current command, return with just the help token
                return command, ["help"]
                
            # If no subcommands, we're done
            if not command.subcommands:
                logger.debug(f"No more subcommands for {command.name}, returning with args: {remaining_parts}")
                break
                            
            # Check if the next part is a valid subcommand
            next_part = remaining_parts[0].lower()
            if next_part in command.subcommands:
                # It's a subcommand, move to it and continue
                logger.debug(f"Found valid subcommand: {next_part} for command {command.name}")
                command = command.subcommands[next_part]
                command_path.append(next_part)
                logger.debug(f"Moving to subcommand: {command.name}, updated path: {command_path}")
                remaining_parts.pop(0)  # Remove the processed part
            else:
                # Not a subcommand, so these are arguments for the current command
                logger.debug(f"No subcommand found for '{next_part}', treating as argument to {command.name}")
                break
        
        logger.debug(f"_find_deepest_command finished: command={command.name}, remaining_parts={remaining_parts}")
        return command, remaining_parts
    
    def _route_subcommand(self, parent_command: Command, subcommand_parts: List[str], 
                         context: Dict[str, Any]) -> CommandResponse:
        """Route to a subcommand of the given parent command.
        
        Note: This method is maintained for backward compatibility.
        New code should use the _find_deepest_command method instead.
        
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
        """Show help text for all available top-level commands.
        
        Returns:
            CommandResponse: A formatted help response.
        """
        if self.help_format == 'block_kit':
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Available Commands"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Here are the commands you can use:"
                    }
                }
            ]
            
            command_blocks = []
            for cmd_name, cmd in sorted(self.top_level_commands.items()):
                # Get short description
                short_desc = cmd.short_help
                if not short_desc and cmd.__doc__:
                    short_desc = cmd.__doc__.strip().split('\n')[0]
                
                command_blocks.append(f"• `{cmd_name}`: {short_desc}")
            
            if command_blocks:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(command_blocks)
                    }
                })
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Use `<command> help` for more details on a specific command."
                }
            })
            
            return CommandResponse.with_blocks(blocks)
        else:
            # Text format
            help_text = "*Available Commands:*\n\n"
            
            for cmd_name, cmd in sorted(self.top_level_commands.items()):
                # Get short description
                short_desc = cmd.short_help
                if not short_desc and cmd.__doc__:
                    short_desc = cmd.__doc__.strip().split('\n')[0]
                
                help_text += f"• `{cmd_name}`: {short_desc}\n"
            
            help_text += "\nUse `<command> help` for more details on a specific command."
            
            return CommandResponse(help_text)
