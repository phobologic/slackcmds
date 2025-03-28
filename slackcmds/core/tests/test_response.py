"""Tests for the CommandResponse class."""

import pytest
from slackcmds.core.response import CommandResponse
from slackcmds.core import block_kit


def test_command_response_init():
    """Test CommandResponse initialization."""
    # Test with text content
    response = CommandResponse("Test message")
    assert response.content == "Test message"
    assert response.success is True
    assert response.ephemeral is True
    
    # Test with Block Kit content
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]
    response = CommandResponse(blocks, success=False, ephemeral=False)
    assert response.content == blocks
    assert response.success is False
    assert response.ephemeral is False


def test_as_dict():
    """Test CommandResponse.as_dict() method."""
    # Test with text content
    response = CommandResponse("Test message")
    result = response.as_dict()
    assert result["text"] == "Test message"
    assert result["response_type"] == "ephemeral"
    
    # Test with Block Kit content and in_channel
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]
    response = CommandResponse(blocks, ephemeral=False)
    result = response.as_dict()
    assert result["blocks"] == blocks
    assert result["response_type"] == "in_channel"


def test_error():
    """Test CommandResponse.error() factory method."""
    response = CommandResponse.error("Something went wrong")
    
    assert response.content == ":x: Error: Something went wrong"
    assert response.success is False
    assert response.ephemeral is True


def test_success():
    """Test CommandResponse.success() factory method."""
    # Test with default ephemeral=True
    response = CommandResponse.success("Operation completed")
    
    assert response.content == ":white_check_mark: Operation completed"
    assert response.success is True
    assert response.ephemeral is True
    
    # Test with ephemeral=False
    response = CommandResponse.success("Announcement", ephemeral=False)
    assert response.ephemeral is False


def test_with_blocks():
    """Test CommandResponse.with_blocks() factory method."""
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": "Block content"}}
    ]
    response = CommandResponse.with_blocks(blocks, success=True, ephemeral=False)
    
    assert response.content == blocks
    assert response.success is True
    assert response.ephemeral is False


def test_error_blocks():
    """Test CommandResponse.error_blocks() factory method."""
    response = CommandResponse.error_blocks("Something went wrong")
    
    assert isinstance(response.content, list)
    assert len(response.content) == 1
    assert response.content[0]["type"] == "section"
    assert ":x: Error: Something went wrong" in response.content[0]["text"]["text"]
    assert response.success is False


def test_success_blocks():
    """Test CommandResponse.success_blocks() factory method."""
    response = CommandResponse.success_blocks("Operation completed")
    
    assert isinstance(response.content, list)
    assert len(response.content) == 1
    assert response.content[0]["type"] == "section"
    assert ":white_check_mark: Operation completed" in response.content[0]["text"]["text"]
    assert response.success is True
    assert response.ephemeral is True
    
    # Test with ephemeral=False
    response = CommandResponse.success_blocks("Announcement", ephemeral=False)
    assert response.ephemeral is False


def test_information():
    """Test CommandResponse.information() factory method."""
    response = CommandResponse.information(
        "System Status",
        ["Database: Online", "API: Operational"]
    )
    
    assert isinstance(response.content, list)
    
    # Find header block
    header = next((b for b in response.content if b["type"] == "header"), None)
    assert header is not None
    assert header["text"]["text"] == "System Status"
    
    # Find section blocks
    sections = [b for b in response.content if b["type"] == "section"]
    assert len(sections) >= 2
    
    # Check for section content
    section_texts = [s["text"]["text"] for s in sections]
    assert any("Database: Online" in text for text in section_texts)
    assert any("API: Operational" in text for text in section_texts)


def test_confirmation():
    """Test CommandResponse.confirmation() factory method."""
    choices = [
        block_kit.button("Yes", "confirm", style="primary"),
        block_kit.button("No", "cancel", style="danger")
    ]
    
    response = CommandResponse.confirmation(
        "Confirm Action",
        "Are you sure you want to proceed?",
        choices
    )
    
    assert isinstance(response.content, list)
    
    # Find header block
    header = next((b for b in response.content if b["type"] == "header"), None)
    assert header is not None
    assert header["text"]["text"] == "Confirm Action"
    
    # Find message section
    message = next((b for b in response.content if b["type"] == "section"), None)
    assert message is not None
    assert message["text"]["text"] == "Are you sure you want to proceed?"
    
    # Find actions block
    actions = next((b for b in response.content if b["type"] == "actions"), None)
    assert actions is not None
    assert len(actions["elements"]) == 2
    
    # Check button details
    assert actions["elements"][0]["text"]["text"] == "Yes"
    assert actions["elements"][0]["style"] == "primary"
    assert actions["elements"][1]["text"]["text"] == "No"
    assert actions["elements"][1]["style"] == "danger"


def test_table():
    """Test CommandResponse.table() factory method."""
    headers = ["Name", "Role", "Status"]
    rows = [
        ["Alice", "Admin", "Active"],
        ["Bob", "User", "Inactive"]
    ]
    
    response = CommandResponse.table("Users", headers, rows)
    
    assert isinstance(response.content, list)
    
    # Find header block
    header = next((b for b in response.content if b["type"] == "header"), None)
    assert header is not None
    assert header["text"]["text"] == "Users"
    
    # Find table section
    table = next((b for b in response.content if b["type"] == "section"), None)
    assert table is not None
    
    # Check table content
    table_text = table["text"]["text"]
    assert "| Name | Role | Status |" in table_text
    assert "| Alice | Admin | Active |" in table_text
    assert "| Bob | User | Inactive |" in table_text


def test_form():
    """Test CommandResponse.form() factory method."""
    input_elements = [
        block_kit.input_block(
            "Username",
            block_kit.plain_text_input("username", placeholder="Enter username")
        ),
        block_kit.input_block(
            "Email",
            block_kit.plain_text_input("email", placeholder="Enter email")
        )
    ]
    
    response = CommandResponse.form("Add User", input_elements)
    
    assert isinstance(response.content, list)
    
    # Find header block
    header = next((b for b in response.content if b["type"] == "header"), None)
    assert header is not None
    assert header["text"]["text"] == "Add User"
    
    # Find input blocks
    inputs = [b for b in response.content if b["type"] == "input"]
    assert len(inputs) == 2
    
    # Check input labels
    input_labels = [i["label"]["text"] for i in inputs]
    assert "Username" in input_labels
    assert "Email" in input_labels
    
    # Find actions block
    actions = next((b for b in response.content if b["type"] == "actions"), None)
    assert actions is not None
    
    # Check button details
    assert actions["elements"][0]["text"]["text"] == "Submit"
    assert actions["elements"][0]["style"] == "primary"
    assert actions["elements"][1]["text"]["text"] == "Cancel"
    assert actions["elements"][1]["style"] == "danger"
