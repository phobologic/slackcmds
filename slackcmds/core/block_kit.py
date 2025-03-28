"""
Block Kit builder utilities.

This module provides helper methods for building common Slack Block Kit components
that can be used in command responses.
"""
from typing import Dict, List, Optional, Union, Any


def header(text: str) -> Dict[str, Any]:
    """Create a header block.
    
    Args:
        text: The text to display in the header (plain text only).
        
    Returns:
        A header block object.
    """
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text
        }
    }


def section(text: str, markdown: bool = True, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a section block.
    
    Args:
        text: The text to display in the section.
        markdown: Whether the text should be formatted as markdown.
        fields: Optional list of field text strings to add as columns.
        
    Returns:
        A section block object.
    """
    text_object = {
        "type": "mrkdwn" if markdown else "plain_text",
        "text": text
    }
    
    block = {
        "type": "section",
        "text": text_object
    }
    
    if fields:
        block["fields"] = [
            {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": field
            } for field in fields
        ]
    
    return block


def divider() -> Dict[str, str]:
    """Create a divider block.
    
    Returns:
        A divider block object.
    """
    return {"type": "divider"}


def context(elements: List[str], markdown: bool = True) -> Dict[str, Any]:
    """Create a context block with text elements.
    
    Args:
        elements: List of text strings to add as context elements.
        markdown: Whether the elements should be formatted as markdown.
        
    Returns:
        A context block object.
    """
    return {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": element
            } for element in elements
        ]
    }


def image(image_url: str, alt_text: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Create an image block.
    
    Args:
        image_url: URL of the image.
        alt_text: Alt text for the image.
        title: Optional title for the image.
        
    Returns:
        An image block object.
    """
    block = {
        "type": "image",
        "image_url": image_url,
        "alt_text": alt_text
    }
    
    if title:
        block["title"] = {
            "type": "plain_text",
            "text": title
        }
    
    return block


def actions(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create an actions block.
    
    Args:
        elements: List of interactive elements.
        
    Returns:
        An actions block object.
    """
    return {
        "type": "actions",
        "elements": elements
    }


def button(text: str, action_id: str, value: Optional[str] = None, 
           style: Optional[str] = None) -> Dict[str, Any]:
    """Create a button element.
    
    Args:
        text: Text to display on the button.
        action_id: Action identifier for the button.
        value: Optional value to include with the action.
        style: Optional button style ('primary', 'danger', or None for default).
        
    Returns:
        A button element object.
    """
    button_obj = {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": text
        },
        "action_id": action_id
    }
    
    if value:
        button_obj["value"] = value
    
    if style in ("primary", "danger"):
        button_obj["style"] = style
    
    return button_obj


def option(text: str, value: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create an option object for select menus.
    
    Args:
        text: Text to display for the option.
        value: Value to be included with the action.
        description: Optional description of the option.
        
    Returns:
        An option object.
    """
    option_obj = {
        "text": {
            "type": "plain_text",
            "text": text
        },
        "value": value
    }
    
    if description:
        option_obj["description"] = {
            "type": "plain_text",
            "text": description
        }
    
    return option_obj


def select_menu(placeholder: str, action_id: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a select menu element.
    
    Args:
        placeholder: Placeholder text to show when no selection.
        action_id: Action identifier for the select menu.
        options: List of option objects created with the option() function.
        
    Returns:
        A select menu element object.
    """
    return {
        "type": "static_select",
        "placeholder": {
            "type": "plain_text",
            "text": placeholder
        },
        "action_id": action_id,
        "options": options
    }


def input_block(label: str, element: Dict[str, Any], block_id: Optional[str] = None, 
                hint: Optional[str] = None, optional: bool = False) -> Dict[str, Any]:
    """Create an input block.
    
    Args:
        label: Label for the input.
        element: Input element (e.g., select menu, text input).
        block_id: Optional block identifier.
        hint: Optional hint text.
        optional: Whether this input is optional.
        
    Returns:
        An input block object.
    """
    input_obj = {
        "type": "input",
        "label": {
            "type": "plain_text",
            "text": label
        },
        "element": element,
        "optional": optional
    }
    
    if block_id:
        input_obj["block_id"] = block_id
    
    if hint:
        input_obj["hint"] = {
            "type": "plain_text",
            "text": hint
        }
    
    return input_obj


def plain_text_input(action_id: str, placeholder: Optional[str] = None, 
                    initial_value: Optional[str] = None, 
                    multiline: bool = False) -> Dict[str, Any]:
    """Create a plain text input element.
    
    Args:
        action_id: Action identifier for the input.
        placeholder: Optional placeholder text.
        initial_value: Optional initial value.
        multiline: Whether the input should be multiline.
        
    Returns:
        A plain text input element object.
    """
    text_input = {
        "type": "plain_text_input",
        "action_id": action_id,
        "multiline": multiline
    }
    
    if placeholder:
        text_input["placeholder"] = {
            "type": "plain_text",
            "text": placeholder
        }
    
    if initial_value:
        text_input["initial_value"] = initial_value
    
    return text_input


def confirmation_dialog(title: str, text: str, confirm: str, deny: str) -> Dict[str, Any]:
    """Create a confirmation dialog object.
    
    Args:
        title: Title of the confirmation dialog.
        text: Text to display in the dialog.
        confirm: Text for the confirmation button.
        deny: Text for the cancel button.
        
    Returns:
        A confirmation dialog object.
    """
    return {
        "title": {
            "type": "plain_text",
            "text": title
        },
        "text": {
            "type": "plain_text",
            "text": text
        },
        "confirm": {
            "type": "plain_text",
            "text": confirm
        },
        "deny": {
            "type": "plain_text",
            "text": deny
        }
    }


def create_message_template(header_text: Optional[str] = None, 
                           sections: Optional[List[str]] = None,
                           context_elements: Optional[List[str]] = None,
                           include_dividers: bool = True) -> List[Dict[str, Any]]:
    """Create a template for a message with common components.
    
    Args:
        header_text: Optional header text.
        sections: Optional list of section texts.
        context_elements: Optional list of context elements.
        include_dividers: Whether to include dividers between sections.
        
    Returns:
        A list of Block Kit blocks.
    """
    blocks = []
    
    if header_text:
        blocks.append(header(header_text))
        if include_dividers:
            blocks.append(divider())
    
    if sections:
        for section_text in sections:
            blocks.append(section(section_text))
            if include_dividers and sections.index(section_text) < len(sections) - 1:
                blocks.append(divider())
    
    if context_elements:
        if blocks and include_dividers:
            blocks.append(divider())
        blocks.append(context(context_elements))
    
    return blocks 