"""
Command response handling.

This module contains the CommandResponse class used to format
and standardize responses from command execution.
"""
from typing import Any, Dict, List, Optional, Union
from slackcmds.core import block_kit


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
    
    @classmethod
    def error_blocks(cls, message: str) -> "CommandResponse":
        """Create a Block Kit formatted error response.
        
        Args:
            message: The error message to display.
            
        Returns:
            CommandResponse: A Block Kit error response.
        """
        blocks = [
            block_kit.section(f":x: Error: {message}")
        ]
        return cls.with_blocks(blocks, success=False)
    
    @classmethod
    def success_blocks(cls, message: str, ephemeral: bool = True) -> "CommandResponse":
        """Create a Block Kit formatted success response.
        
        Args:
            message: The success message to display.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A Block Kit success response.
        """
        blocks = [
            block_kit.section(f":white_check_mark: {message}")
        ]
        return cls.with_blocks(blocks, success=True, ephemeral=ephemeral)
    
    @classmethod
    def information(cls, title: str, details: List[str], ephemeral: bool = True) -> "CommandResponse":
        """Create an informational message with a title and details.
        
        Args:
            title: The title of the information.
            details: List of text strings with details.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: An informational response.
        """
        blocks = block_kit.create_message_template(
            header_text=title,
            sections=details
        )
        return cls.with_blocks(blocks, success=True, ephemeral=ephemeral)
    
    @classmethod
    def confirmation(cls, title: str, message: str, choices: List[Dict[str, Any]], 
                    ephemeral: bool = True) -> "CommandResponse":
        """Create a confirmation message with interactive buttons.
        
        Args:
            title: The title of the confirmation.
            message: The message to display.
            choices: List of button elements created with block_kit.button().
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A confirmation response with buttons.
        """
        blocks = [
            block_kit.header(title),
            block_kit.section(message),
            block_kit.actions(choices)
        ]
        return cls.with_blocks(blocks, success=True, ephemeral=ephemeral)
    
    @classmethod
    def table(cls, title: str, headers: List[str], rows: List[List[str]], 
             ephemeral: bool = True) -> "CommandResponse":
        """Create a message formatted as a table.
        
        Args:
            title: The title of the table.
            headers: List of column headers.
            rows: List of rows, where each row is a list of column values.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A table-formatted response.
        """
        blocks = [block_kit.header(title)]
        
        # Format table as markdown
        table_text = ""
        
        # Add headers
        header_row = "| " + " | ".join(headers) + " |"
        table_text += header_row + "\n"
        
        # Add separator
        separator_row = "| " + " | ".join(["---" for _ in headers]) + " |"
        table_text += separator_row + "\n"
        
        # Add data rows
        for row in rows:
            data_row = "| " + " | ".join(row) + " |"
            table_text += data_row + "\n"
        
        blocks.append(block_kit.section(table_text))
        
        return cls.with_blocks(blocks, success=True, ephemeral=ephemeral)
    
    @classmethod
    def form(cls, title: str, input_elements: List[Dict[str, Any]], 
            submit_label: str = "Submit", cancel_label: str = "Cancel",
            ephemeral: bool = True) -> "CommandResponse":
        """Create a form with input elements.
        
        Args:
            title: The title of the form.
            input_elements: List of input block elements created with block_kit.input_block().
            submit_label: Label for the submit button.
            cancel_label: Label for the cancel button.
            ephemeral: Whether the response should be visible only to the user.
            
        Returns:
            CommandResponse: A form response.
        """
        blocks = [
            block_kit.header(title),
            *input_elements,
            block_kit.actions([
                block_kit.button(submit_label, "submit", style="primary"),
                block_kit.button(cancel_label, "cancel", style="danger")
            ])
        ]
        return cls.with_blocks(blocks, success=True, ephemeral=ephemeral)
