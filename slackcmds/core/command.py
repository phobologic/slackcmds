"""
Command base class implementation.

This module contains the base Command class that all commands inherit from,
providing common functionality for execution, validation, and help text.
"""

import logging
import traceback
from typing import Dict, List, Optional, Union, Any, TypeVar, cast

from .response import CommandResponse

logger = logging.getLogger("slackcmds.command")

T = TypeVar('T', bound='Command')


class Command:
    """Base class for all command handlers.
    
    This class serves as the foundation for all commands in the system.
    It provides common functionality like help text generation and 
    subcommand registration.
    
    Attributes:
        name: The name of the command.
        subcommands: Dictionary of registered subcommands.
        short_help: Short description of the command.
        long_help: Detailed help text for the command.
    """
    
    def __init__(self) -> None:
        """Initialize a new Command instance."""
        self.name: Optional[str] = None
        self.subcommands: Dict[str, 'Command'] = {}
        self.short_help: Optional[str] = None
        self.long_help: Optional[str] = None
    
    def _set_name(self, name: str) -> T:
        """Set the command name (called during registration).
        
        Args:
            name: The name to set for this command.
            
        Returns:
            Self for method chaining.
        """
        self.name = name
        return cast(T, self)
    
    def set_help(self, short_help: Optional[str] = None, long_help: Optional[str] = None) -> T:
        """Override the default help text generated from docstrings.
        
        Args:
            short_help: Brief description of the command.
            long_help: Detailed help text for the command.
            
        Returns:
            Self for method chaining.
        """
        self.short_help = short_help
        self.long_help = long_help
        return cast(T, self)
        
    def execute(self, context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """Execute the command logic.
        
        This method should be overridden by subclasses to implement
        command-specific behavior.
        
        Args:
            context: Dictionary containing execution context information.
            
        Returns:
            CommandResponse: The result of command execution.
        """
        try:
            logger.debug(f"Executing command: {self.name}")
            
            # Initialize context if None
            if context is None:
                context = {}
            
            # Validate input if needed
            validation_result = self.validate(context)
            if not validation_result.success:
                return validation_result
            
            # If there are subcommands but none specified, show help
            if self.subcommands and not context.get('subcommand'):
                return self.show_help()
            
            # Default implementation for commands without overridden execute
            return CommandResponse(
                f"Command '{self.name}' doesn't have an implementation.",
                success=False
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in {self.name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            return CommandResponse(
                f"An unexpected error occurred: {str(e)}",
                success=False
            )
    
    def validate(self, context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """Validate command input before execution.
        
        Override this method to implement custom validation logic.
        
        Args:
            context: Dictionary containing execution context information.
            
        Returns:
            CommandResponse: A response object indicating validation success/failure.
        """
        return CommandResponse("Input valid", success=True)
    
    def show_help(self, specific_subcommand: Optional[str] = None) -> CommandResponse:
        """Show detailed help for this command or a specific subcommand.
        
        Args:
            specific_subcommand: Name of a specific subcommand to show help for.
            
        Returns:
            CommandResponse: A formatted help response.
        """
        # Generate title
        title = f"Help: {self.name}"
        
        # Get command description from docstring or override
        command_description = self.long_help
        if not command_description and self.__doc__:
            command_description = self.__doc__.strip()
        
        # Generate help text
        help_text = f"*{title}*\n\n"
        
        if command_description:
            help_text += f"{command_description}\n\n"
        
        # Add subcommands list if any
        if self.subcommands:
            help_text += "*Available Subcommands:*\n"
            for subcmd_name, subcmd in self.subcommands.items():
                # Get short description from subcommand
                short_desc = subcmd.short_help
                if not short_desc and subcmd.__doc__:
                    short_desc = subcmd.__doc__.strip().split('\n')[0]
                
                help_text += f"• `{subcmd_name}`: {short_desc}\n"
            
            help_text += f"\nUse `{self.name} help <subcommand>` for more details on a specific subcommand."
        
        return CommandResponse(help_text)
    
    def register_subcommand(self, name: str, command_instance: 'Command') -> 'Command':
        """Register a subcommand.
        
        Args:
            name: Name of the subcommand.
            command_instance: Instance of Command class to handle the subcommand.
            
        Returns:
            The registered command instance for method chaining.
        """
        command_instance._set_name(f"{self.name} {name}")
        self.subcommands[name] = command_instance
        logger.debug(f"Registered subcommand '{name}' for '{self.name}'")
        return command_instance
