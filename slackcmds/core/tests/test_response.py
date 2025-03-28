"""Tests for the CommandResponse class."""

import pytest
from slackcmds.core.response import CommandResponse


def test_command_response_init():
    """Test CommandResponse initialization."""
    response = CommandResponse("Test message")
    assert response.content == "Test message"
    assert response.success is True
    assert response.ephemeral is True


def test_command_response_as_dict_text():
    """Test CommandResponse.as_dict() with text content."""
    response = CommandResponse("Test message")
    result = response.as_dict()
    
    assert result == {
        "text": "Test message",
        "response_type": "ephemeral"
    }


def test_command_response_as_dict_blocks():
    """Test CommandResponse.as_dict() with Block Kit content."""
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test block"}}]
    response = CommandResponse(blocks, ephemeral=False)
    result = response.as_dict()
    
    assert result == {
        "blocks": blocks,
        "response_type": "in_channel"
    }


def test_command_response_error():
    """Test CommandResponse.error() factory method."""
    response = CommandResponse.error("Something went wrong")
    
    assert response.content == ":x: Error: Something went wrong"
    assert response.success is False
    assert response.ephemeral is True


def test_command_response_success():
    """Test CommandResponse.success() factory method."""
    response = CommandResponse.success("Operation completed", ephemeral=False)
    
    assert response.content == ":white_check_mark: Operation completed"
    assert response.success is True
    assert response.ephemeral is False


def test_command_response_with_blocks():
    """Test CommandResponse.with_blocks() factory method."""
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test block"}}]
    response = CommandResponse.with_blocks(blocks, success=True, ephemeral=False)
    
    assert response.content == blocks
    assert response.success is True
    assert response.ephemeral is False
