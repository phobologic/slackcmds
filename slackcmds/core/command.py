"""
Command base class implementation.

This module contains the base Command class that all commands inherit from,
providing common functionality for execution, validation, and help text.
"""

import logging
import traceback
from typing import Dict, List, Optional, Union, Any, TypeVar, cast, Tuple, Generic

from .response import CommandResponse
from . import validation
from .validation import Parameter

logger = logging.getLogger("slackcmds.command")

T = TypeVar('T', bound='Command')


class Command:
    """Base class for all command handlers.
    
    This class serves as the foundation for all commands in the system.
    It provides common functionality like help text generation and 
    subcommand registration.
    
    IMPORTANT: When implementing custom commands, ONLY override _execute_impl().
    NEVER override execute() as it handles critical functionality like help text 
    processing and validation. Overriding execute() will break these features.
    
    Attributes:
        name: The name of the command.
        subcommands: Dictionary of registered subcommands.
        short_help: Short description of the command.
        long_help: Detailed help text for the command.
        usage_example: Example of how to use the command.
        use_block_kit: Whether to use Block Kit formatting for help text.
        parameters: List of parameter definitions for validation.
    """
    
    def __init__(self) -> None:
        """Initialize a new Command instance."""
        self.name: Optional[str] = None
        self.subcommands: Dict[str, 'Command'] = {}
        self.short_help: Optional[str] = None
        self.long_help: Optional[str] = None
        self.usage_example: Optional[str] = None
        self.use_block_kit: bool = False
        # Flag to indicate if this command accepts arguments or requires valid subcommands
        # When True, any tokens are passed to _execute_impl to handle as arguments
        # When False, the first token must be a valid subcommand, otherwise an error is shown
        # By default, commands without subcommands accept arguments, and commands with subcommands don't
        self.accepts_arguments: bool = True
        # Parameter definitions for validation
        self.parameters: List[Parameter] = []
    
    def _set_name(self, name: str) -> T:
        """Set the command name (called during registration).
        
        Args:
            name: The name to set for this command.
            
        Returns:
            Self for method chaining.
        """
        self.name = name
        return cast(T, self)
    
    def set_help(self, short_help: Optional[str] = None, 
                long_help: Optional[str] = None,
                usage_example: Optional[str] = None) -> T:
        """Override the default help text generated from docstrings.
        
        Args:
            short_help: Short description of the command.
            long_help: Detailed help text for the command.
            usage_example: Example of how to use the command.
            
        Returns:
            Self for method chaining.
        """
        self.short_help = short_help
        self.long_help = long_help
        self.usage_example = usage_example
        return cast(T, self)
    
    def add_parameter(self, parameter: Parameter) -> T:
        """Add a parameter to this command.
        
        Args:
            parameter: The Parameter object to add.
            
        Returns:
            The command instance for chaining.
        """
        if not self.accepts_arguments:
            logger.warning(
                "Adding parameters to a command that doesn't accept arguments. "
                "Set accepts_arguments=True in the command constructor."
            )
            self.accepts_arguments = True
        
        self.parameters.append(parameter)
        return cast(T, self)
    
    def add_parameters(self, parameters: List[Parameter]) -> T:
        """Add multiple parameters to this command.
        
        Args:
            parameters: The parameters to add.
            
        Returns:
            Self for method chaining.
        """
        if not self.accepts_arguments and parameters:
            logger.warning(
                "Adding parameters to a command that doesn't accept arguments. "
                "Set accepts_arguments=True in the command constructor."
            )
            self.accepts_arguments = True
            
        self.parameters.extend(parameters)
        return cast(T, self)
    
    def execute(self, context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """Execute the command logic.
        
        This is the main entry point for command execution. It handles common
        functionality like help text processing and validation.
        
        WARNING: DO NOT OVERRIDE THIS METHOD IN SUBCLASSES! 
        Always override _execute_impl() instead to implement command-specific behavior.
        Overriding this method will break help handling and other core functionality.
        
        Args:
            context: Dictionary containing execution context information.
            
        Returns:
            CommandResponse: The result of command execution.
        """
        try:
            logger.debug(f"Executing command: {self.name} with context: {context}")
            
            # Initialize context if None
            if context is None:
                context = {}
                
            # HIGHEST PRIORITY: Check if this is a help request
            # Look for 'help' as the first token
            tokens = context.get("tokens", [])
            if tokens and tokens[0].lower() == "help":
                logger.debug(f"Help token detected in command {self.name} - tokens: {tokens}")
                # If there's a second token, it might be a specific subcommand
                if len(tokens) > 1 and tokens[1] in self.subcommands:
                    subcmd_name = tokens[1]
                    logger.debug(f"Help requested for specific subcommand: {subcmd_name}")
                    return self.subcommands[subcmd_name].show_help()
                # Return general help for this command
                logger.debug(f"Showing general help for command: {self.name}")
                return self.show_help()
            
            # Validate input if needed
            validation_result = self.validate(context)
            if not validation_result.success:
                logger.debug(f"Validation failed for command {self.name}")
                return validation_result
            
            # If this command has subcommands AND doesn't accept arguments,
            # check if the first token is a valid subcommand
            if self.subcommands and not self.accepts_arguments and tokens:
                first_token = tokens[0].lower()
                if first_token not in self.subcommands:
                    logger.debug(f"Invalid subcommand '{first_token}' detected for command {self.name}")
                    return self.show_invalid_subcommand_error(first_token)
                            
            # If there are subcommands but no explicit command execution,
            # default to showing help
            if self.subcommands and not self._has_custom_execution():
                logger.debug(f"Command {self.name} has subcommands but no custom execution - showing help")
                return self.show_help()
            
            # Check for implementation
            if self._has_custom_execution():
                # If we got here, this is a valid command execution
                logger.debug(f"Proceeding with execution of command {self.name} using _execute_impl")
                return self._execute_impl(context)
            
            # No implementation found
            logger.debug(f"Command {self.name} has no implementation")
            # Additional detailed logging for better debugging
            logger.debug(f"Command class: {self.__class__.__name__}")
            logger.debug(f"Command's direct methods: {list(self.__class__.__dict__.keys())}")
            logger.debug(f"Parent class: {self.__class__.__bases__[0].__name__}")
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
    
    def _has_custom_execution(self) -> bool:
        """Check if this command has a custom execute implementation.
        
        Returns:
            bool: True if the _execute_impl method is overridden, False otherwise.
        """
        # Get the method from the instance's class
        cmd_impl = self.__class__.__dict__.get('_execute_impl')
        
        # Check if the method exists in this class (not inherited)
        # and that this isn't the base Command class (which defines _execute_impl but isn't a custom implementation)
        has_impl = cmd_impl is not None and self.__class__ is not Command
        
        logger.debug(f"Command {self.name} (class: {self.__class__.__name__}) - " 
                  f"has custom implementation: {has_impl}")
        
        return has_impl
    
    def _execute_impl(self, context: Dict[str, Any]) -> CommandResponse:
        """Actual implementation of command execution.
        
        This is the method that should be overridden by subclasses to implement
        command-specific behavior. Overriding this method ensures that help text
        and validation logic in the base execute() method are preserved.
        
        Args:
            context: Dictionary containing execution context information.
        
        Returns:
            CommandResponse: The result of command execution.
        """
        # This should never be called directly, as _has_custom_execution would return False
        # and the execute method would show help or return an error
        return CommandResponse(
            f"Command '{self.name}' doesn't have an implementation.",
            success=False
        )
    
    def validate(self, context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """Validate command input before execution.
        
        This method performs validation of command parameters based on the 
        parameter definitions specified for this command. It can be overridden
        by subclasses to implement custom validation logic.
        
        Args:
            context: Dictionary containing execution context information.
            
        Returns:
            CommandResponse: A response object indicating validation success/failure.
        """
        if not self.parameters:
            return CommandResponse("Input valid", success=True)
        
        # If we have parameter definitions, use the validation framework
        if context is not None and "tokens" in context:
            tokens = context.get("tokens", [])
            named_params = context.get("named_params", {})
            
            # Validate parameters
            result = validation.validate_params(self.parameters, tokens, named_params)
            
            # Add validated parameters to context for use in command execution
            if result.valid:
                context["validated_params"] = result.validated_params
                return CommandResponse("Input valid", success=True)
            else:
                # Return validation errors
                return result.as_command_response()
        
        # No tokens to validate
        return CommandResponse("Input valid", success=True)
    
    def show_invalid_subcommand_error(self, invalid_arg: str) -> CommandResponse:
        """Generate error response for invalid subcommand.
        
        Args:
            invalid_arg: The invalid subcommand or argument that was provided.
            
        Returns:
            CommandResponse: Error response with help text.
        """
        # Generate help text to append after error
        title = f"Help: {self.name}"
        
        # Get command description from docstring or override
        command_description = self.long_help
        if not command_description and self.__doc__:
            command_description = self.__doc__.strip()
        
        # Get usage example
        usage = self.usage_example
        if not usage and self.name:
            usage = f"{self.name}"
            
        # If we're using Block Kit formatting
        if self.use_block_kit:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: Error: '{invalid_arg}' is not a valid subcommand for '{self.name}'."
                    }
                },
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                }
            ]
            
            # Add description if available
            if command_description:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": command_description
                    }
                })
            
            # Add usage example if available
            if usage:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Usage:*\n`{usage}`"
                    }
                })
            
            # Add subcommands if any
            if self.subcommands:
                subcommand_text = "*Available Subcommands:*\n"
                for subcmd_name, subcmd in self.subcommands.items():
                    # Get short description from subcommand
                    short_desc = subcmd.short_help
                    if not short_desc and subcmd.__doc__:
                        short_desc = subcmd.__doc__.strip().split('\n')[0]
                    
                    subcommand_text += f"• `{subcmd_name}`: {short_desc}\n"
                
                subcommand_text += f"\nUse `{self.name} help <subcommand>` for more details on a specific subcommand."
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": subcommand_text
                    }
                })
            
            # Add divider and context
            blocks.append({
                "type": "divider"
            })
            
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Type `help` for a list of all commands."
                    }
                ]
            })
            
            return CommandResponse.with_blocks(blocks, success=False)
            
        # Generate text-based help
        error_message = f":x: Error: '{invalid_arg}' is not a valid subcommand for '{self.name}'.\n\n"
        error_message += f"*{title}*\n\n"
        
        if command_description:
            error_message += f"{command_description}\n\n"
        
        # Add usage example
        if usage:
            error_message += f"*Usage:*\n`{usage}`\n\n"
        
        # Add subcommands list if any
        if self.subcommands:
            error_message += "*Available Subcommands:*\n"
            for subcmd_name, subcmd in self.subcommands.items():
                # Get short description from subcommand
                short_desc = subcmd.short_help
                if not short_desc and subcmd.__doc__:
                    short_desc = subcmd.__doc__.strip().split('\n')[0]
                
                error_message += f"• `{subcmd_name}`: {short_desc}\n"
            
            error_message += f"\nUse `{self.name} help <subcommand>` for more details on a specific subcommand."
        
        return CommandResponse(error_message, success=False)
    
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
        
        # Get usage example
        usage = self.usage_example
        if not usage and self.name:
            usage = f"{self.name}"
            
        # If we're using Block Kit formatting
        if self.use_block_kit:
            return self._generate_block_kit_help(title, command_description, usage)
        
        # Generate text-based help
        help_text = f"*{title}*\n\n"
        
        if command_description:
            help_text += f"{command_description}\n\n"
        
        # Add usage example
        if usage:
            help_text += f"*Usage:*\n`{usage}`\n\n"
        
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
    
    def _generate_block_kit_help(self, title: str, description: Optional[str] = None, 
                                usage: Optional[str] = None) -> CommandResponse:
        """Generate Block Kit formatted help text.
        
        Args:
            title: The title of the help text.
            description: Detailed description of the command.
            usage: Example usage of the command.
            
        Returns:
            CommandResponse: A response with Block Kit formatted help.
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            }
        ]
        
        # Add description if available
        if description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": description
                }
            })
        
        # Add usage example if available
        if usage:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Usage:*\n`{usage}`"
                }
            })
        
        # Add subcommands if any
        if self.subcommands:
            subcommand_text = "*Available Subcommands:*\n"
            for subcmd_name, subcmd in self.subcommands.items():
                # Get short description from subcommand
                short_desc = subcmd.short_help
                if not short_desc and subcmd.__doc__:
                    short_desc = subcmd.__doc__.strip().split('\n')[0]
                
                subcommand_text += f"• `{subcmd_name}`: {short_desc}\n"
            
            subcommand_text += f"\nUse `{self.name} help <subcommand>` for more details on a specific subcommand."
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": subcommand_text
                }
            })
        
        # Add divider and context
        blocks.append({
            "type": "divider"
        })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Type `help` for a list of all commands."
                }
            ]
        })
        
        return CommandResponse.with_blocks(blocks)
    
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
        # When a command has subcommands, by default it doesn't accept arbitrary arguments
        # (unless explicitly set otherwise)
        if len(self.subcommands) == 1:  # Only set it on first subcommand added
            self.accepts_arguments = False
        logger.debug(f"Registered subcommand '{name}' for '{self.name}'")
        return command_instance
