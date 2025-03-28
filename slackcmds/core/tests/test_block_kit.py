"""Tests for Block Kit builder utilities."""
import pytest
from slackcmds.core import block_kit


def test_header_block():
    """Test creating a header block."""
    block = block_kit.header("Test Header")
    
    assert block["type"] == "header"
    assert block["text"]["type"] == "plain_text"
    assert block["text"]["text"] == "Test Header"


def test_section_block():
    """Test creating a section block."""
    # Test with markdown text
    block = block_kit.section("Test Section")
    
    assert block["type"] == "section"
    assert block["text"]["type"] == "mrkdwn"
    assert block["text"]["text"] == "Test Section"
    
    # Test with plain text
    block = block_kit.section("Test Section", markdown=False)
    assert block["text"]["type"] == "plain_text"
    
    # Test with fields
    fields = ["Field 1", "Field 2"]
    block = block_kit.section("Test Section", fields=fields)
    
    assert "fields" in block
    assert len(block["fields"]) == 2
    assert block["fields"][0]["text"] == "Field 1"
    assert block["fields"][1]["text"] == "Field 2"


def test_divider_block():
    """Test creating a divider block."""
    block = block_kit.divider()
    
    assert block["type"] == "divider"


def test_context_block():
    """Test creating a context block."""
    elements = ["Context 1", "Context 2"]
    block = block_kit.context(elements)
    
    assert block["type"] == "context"
    assert len(block["elements"]) == 2
    assert block["elements"][0]["type"] == "mrkdwn"
    assert block["elements"][0]["text"] == "Context 1"
    
    # Test with plain text
    block = block_kit.context(elements, markdown=False)
    assert block["elements"][0]["type"] == "plain_text"


def test_image_block():
    """Test creating an image block."""
    block = block_kit.image("https://example.com/image.jpg", "Alt text")
    
    assert block["type"] == "image"
    assert block["image_url"] == "https://example.com/image.jpg"
    assert block["alt_text"] == "Alt text"
    
    # Test with title
    block = block_kit.image("https://example.com/image.jpg", "Alt text", "Title")
    assert "title" in block
    assert block["title"]["text"] == "Title"


def test_actions_block():
    """Test creating an actions block."""
    elements = [
        {"type": "button", "text": {"type": "plain_text", "text": "Button 1"}},
        {"type": "button", "text": {"type": "plain_text", "text": "Button 2"}}
    ]
    block = block_kit.actions(elements)
    
    assert block["type"] == "actions"
    assert len(block["elements"]) == 2


def test_button_element():
    """Test creating a button element."""
    button = block_kit.button("Click Me", "button_1")
    
    assert button["type"] == "button"
    assert button["text"]["type"] == "plain_text"
    assert button["text"]["text"] == "Click Me"
    assert button["action_id"] == "button_1"
    
    # Test with value
    button = block_kit.button("Click Me", "button_1", "value_1")
    assert button["value"] == "value_1"
    
    # Test with style
    button = block_kit.button("Click Me", "button_1", style="primary")
    assert button["style"] == "primary"


def test_option_element():
    """Test creating an option element."""
    option = block_kit.option("Option 1", "value_1")
    
    assert option["text"]["type"] == "plain_text"
    assert option["text"]["text"] == "Option 1"
    assert option["value"] == "value_1"
    
    # Test with description
    option = block_kit.option("Option 1", "value_1", "Description")
    assert "description" in option
    assert option["description"]["text"] == "Description"


def test_select_menu_element():
    """Test creating a select menu element."""
    options = [
        block_kit.option("Option 1", "value_1"),
        block_kit.option("Option 2", "value_2")
    ]
    select = block_kit.select_menu("Select an option", "select_1", options)
    
    assert select["type"] == "static_select"
    assert select["placeholder"]["text"] == "Select an option"
    assert select["action_id"] == "select_1"
    assert len(select["options"]) == 2


def test_input_block():
    """Test creating an input block."""
    element = block_kit.plain_text_input("input_1")
    block = block_kit.input_block("Label", element)
    
    assert block["type"] == "input"
    assert block["label"]["text"] == "Label"
    assert block["element"]["action_id"] == "input_1"
    assert block["optional"] is False
    
    # Test with hint and optional
    block = block_kit.input_block("Label", element, hint="Hint text", optional=True)
    assert block["hint"]["text"] == "Hint text"
    assert block["optional"] is True
    
    # Test with block_id
    block = block_kit.input_block("Label", element, block_id="block_1")
    assert block["block_id"] == "block_1"


def test_plain_text_input_element():
    """Test creating a plain text input element."""
    input_element = block_kit.plain_text_input("input_1")
    
    assert input_element["type"] == "plain_text_input"
    assert input_element["action_id"] == "input_1"
    assert input_element["multiline"] is False
    
    # Test with placeholder and initial value
    input_element = block_kit.plain_text_input(
        "input_1", 
        placeholder="Enter text",
        initial_value="Initial value",
        multiline=True
    )
    assert input_element["placeholder"]["text"] == "Enter text"
    assert input_element["initial_value"] == "Initial value"
    assert input_element["multiline"] is True


def test_confirmation_dialog():
    """Test creating a confirmation dialog."""
    dialog = block_kit.confirmation_dialog(
        "Confirm Action", 
        "Are you sure?", 
        "Yes", 
        "No"
    )
    
    assert dialog["title"]["text"] == "Confirm Action"
    assert dialog["text"]["text"] == "Are you sure?"
    assert dialog["confirm"]["text"] == "Yes"
    assert dialog["deny"]["text"] == "No"


def test_create_message_template():
    """Test creating a message template."""
    # Test with all components
    blocks = block_kit.create_message_template(
        header_text="Test Header",
        sections=["Section 1", "Section 2"],
        context_elements=["Created by User"]
    )
    
    assert len(blocks) == 7  # Header, divider, Section1, divider, Section2, divider, Context
    assert blocks[0]["type"] == "header"
    assert blocks[0]["text"]["text"] == "Test Header"
    
    # Find sections
    sections = [b for b in blocks if b["type"] == "section" and b["text"]["text"] in ["Section 1", "Section 2"]]
    assert len(sections) == 2
    
    # Find context
    context = next((b for b in blocks if b["type"] == "context"), None)
    assert context is not None
    assert context["elements"][0]["text"] == "Created by User"
    
    # Test without dividers
    blocks = block_kit.create_message_template(
        header_text="Test Header",
        sections=["Section 1", "Section 2"],
        include_dividers=False
    )
    
    assert len(blocks) == 3  # Header, Section1, Section2
    assert all(b["type"] != "divider" for b in blocks) 