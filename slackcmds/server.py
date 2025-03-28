"""
Server integration with Slack Bolt.

This module provides an example of how to integrate the slackcmds
library with the Slack Bolt framework.
"""

import os
import logging
from typing import Any, Dict, NoReturn
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.ack import Ack
from slack_bolt.context.say import Say

from slackcmds import CommandRegistry

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("slackcmds.server")

# Load environment variables
load_dotenv()

# Initialize the Slack Bolt app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize command registry
registry = CommandRegistry()


def register_commands() -> None:
    """Register commands with the registry.
    
    This function should be implemented to register all available commands
    with the command registry. It is called during server startup.
    """
    # This is where you would register your commands
    # Example: registry.register_command("user", UserCommand())
    logger.debug("No commands registered with the registry")
    pass


@app.command("/slackcmd")
def handle_command(ack: Ack, command: Dict[str, Any], say: Say) -> None:
    """Handle the slash command.
    
    Args:
        ack: The acknowledgment function from Slack Bolt.
        command: The command data from Slack.
        say: The response function from Slack Bolt.
    """
    ack()  # Acknowledge receipt of the command
    
    logger.info(f"Received command: {command['text']}")
    logger.debug(f"Full command payload: {command}")
    
    # Parse command text to extract tokens
    text = command["text"].strip() if command.get("text") else ""
    tokens = []
    
    # Split the command text into tokens
    parts = text.split()
    if len(parts) > 1:  # If we have more than just the command
        tokens = parts[1:]  # Everything after the command name
        logger.debug(f"Extracted tokens: {tokens}")
    
    # Create context object with command information
    context = {
        "user_id": command["user_id"],
        "channel_id": command["channel_id"],
        "team_id": command["team_id"],
        "text": text,
        "tokens": tokens,
        "command": command
    }
    logger.debug(f"Created context: {context}")
    
    # Route the command
    logger.debug(f"Routing command: '{text}'")
    result = registry.route_command(command["text"], context)
    logger.debug(f"Command result: {result.__dict__}")
    
    # Send the response
    logger.debug(f"Sending response: {result.as_dict()}")
    if result.success:
        say(result.as_dict())
    else:
        # Handle error responses
        say(result.as_dict())


def start_server() -> NoReturn:
    """Start the Slack Bolt server.
    
    This function initializes and starts the Slack Bolt server in either
    Socket Mode or HTTP mode based on environment configuration.
    
    Raises:
        ValueError: If required environment variables are missing.
    """
    logger.debug("Initializing server")
    register_commands()
    
    # Check if we're using Socket Mode
    if os.environ.get("SLACK_APP_TOKEN"):
        logger.info("Starting in Socket Mode")
        logger.debug(f"Using app token: {os.environ.get('SLACK_APP_TOKEN')[:10]}***")
        handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
        handler.start()
    else:
        # HTTP mode
        port = int(os.environ.get("PORT", 3000))
        logger.info(f"Starting HTTP server on port {port}")
        logger.debug("HTTP mode selected, no app token provided")
        app.start(port=port)


if __name__ == "__main__":
    start_server()
