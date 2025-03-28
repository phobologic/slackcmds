"""
Basic usage example for slackcmds library.

This example shows how to register commands and handle Slack slash commands.
"""

import os
import logging
from dotenv import load_dotenv
from slack_bolt import App

from slackcmds import CommandRegistry
from slackcmds.commands import UserCommand

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("example")

# Load environment variables
load_dotenv()

# Initialize the Slack Bolt app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize command registry
registry = CommandRegistry()

# Register commands
registry.register_command("user", UserCommand())


@app.command("/slackcmd")
def handle_command(ack, command, say):
    """Handle the slash command."""
    ack()  # Acknowledge receipt of the command
    
    logger.info(f"Received command: {command['text']}")
    
    # Create context object with command information
    context = {
        "user_id": command["user_id"],
        "channel_id": command["channel_id"],
        "team_id": command["team_id"],
        "command": command
    }
    
    # Route the command
    result = registry.route_command(command["text"], context)
    
    # Send the response
    say(result.as_dict())


if __name__ == "__main__":
    # Start the app
    port = int(os.environ.get("PORT", 3000))
    logger.info(f"Starting app on port {port}")
    app.start(port=port) 