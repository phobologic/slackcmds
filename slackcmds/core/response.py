"""
Command response handling.

This module contains the CommandResponse class used to format
and standardize responses from command execution.
"""
from typing import Any, Dict, List, Optional, Union


class CommandResponse:
    """Response object for command execution results.
    
    This class is used to standardize responses from command execution
    and provides methods to format responses for the Slack API.
    
    Attributes:
        content: Text or Block Kit content for the response.
        success: Whether the command was successful.
        ephemeral: Whether the response should be visible only to the user.
    """
    
    def __init__(self, content: Union[str, List[Dict[str, Any]]], success: bool = True, ephemeral: bool = True) -> None:
        """Initialize a new command response.
        
        Args:
            content: Text or Block Kit content for the response.
            success: Whether the command was successful.
            ephemeral: Whether the response should be visible only to the user.
        """
        self.content = content
        self.success = success
        self.ephemeral = ephemeral
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert response to format expected by Slack API.
        
        Returns:
            Dict containing the formatted response for the Slack API.
        """
        if isinstance(self.content, str):
            return {
                "text": self.content,
                "response_type": "ephemeral" if self.ephemeral else "in_channel"
            }
        else:
            # Block Kit format
            return {
                "blocks": self.content,
                "response_type": "ephemeral" if self.ephemeral else "in_channel"
            }
    
    @classmethod
    def error(cls, message: str) -> "CommandResponse":
        """Create a standardized error response.
        
        Args:
            message: The error message to display.
            
        Returns:
            CommandResponse: An error response with the message.
        """
        return cls(f":x: Error: {message}", success=False)
    
    @classmethod
    def success(cls, message: str, ephemeral: bool = True) -> "CommandResponse":
        """Create a standardized success response.
        
        Args:
            message: The success message to display.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A success response with the message.
        """
        return cls(f":white_check_mark: {message}", success=True, ephemeral=ephemeral)
    
    @classmethod
    def with_blocks(cls, blocks: List[Dict[str, Any]], success: bool = True, ephemeral: bool = True) -> "CommandResponse":
        """Create a response with Block Kit blocks.
        
        Args:
            blocks: List of Block Kit blocks.
            success: Whether the command was successful.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A response containing the provided blocks.
        """
        return cls(blocks, success=success, ephemeral=ephemeral)
