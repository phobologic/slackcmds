#!/usr/bin/env python3
"""
Phase 4 Demo: Server Integration with Slack Bolt.

This demo script shows how to integrate the command system with Slack Bolt
for handling slash commands in Slack.

## Setup Instructions

1. Create a Slack App in the Slack API Console (https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "SlackCmds Demo") and select your workspace

2. Set up Socket Mode (recommended for demos)
   - Go to "Socket Mode" in the sidebar
   - Enable Socket Mode
   - Generate an app-level token with "connections:write" scope
   - Save this token (starts with "xapp-") for the SLACK_APP_TOKEN environment variable

3. Set up Slash Commands
   - Go to "Slash Commands" in the sidebar
   - Click "Create New Command"
   - Command: "/demo"
   - Description: "Test the SlackCmds library"
   - Usage hint: "[command] [subcommand]"
   - Check "Escape channels, users, and links sent to your app"
   - Click "Save"

4. Set up Bot Token Scopes
   - Go to "OAuth & Permissions" in the sidebar
   - Under "Scopes" → "Bot Token Scopes", add:
     - commands
     - chat:write
     - chat:write.public

5. Install the App to Your Workspace
   - Go to "Install App" in the sidebar
   - Click "Install to Workspace"
   - Authorize the app
   - Copy the Bot User OAuth Token (starts with "xoxb-")

6. Create a .env file with the following variables:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   SLACK_APP_TOKEN=xapp-your-app-level-token
   # Set to DEBUG for detailed logging (INFO is default)
   LOG_LEVEL=DEBUG
   ```
   - Bot Token: from step 5
   - Signing Secret: found in "Basic Information" → "App Credentials"
   - App Token: from step 2

7. Run this demo:
   ```
   python examples/phase4_demo.py
   ```

Note: This script requires proper Slack API credentials to be set in .env file:
- SLACK_BOT_TOKEN: Your bot token (xoxb-...)
- SLACK_SIGNING_SECRET: Your app signing secret
- SLACK_APP_TOKEN: Your app-level token (xapp-...) for socket mode
- LOG_LEVEL: Set to 'DEBUG' for detailed logging (default is 'INFO')
"""

import os
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.registry import CommandRegistry

# Load environment variables first so we can use them for logging
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("phase4_demo")

# If log level is DEBUG, add a startup message
if logger.level == logging.DEBUG:
    logger.debug("Debug logging enabled via LOG_LEVEL environment variable")

# Define some example commands
class GreetingCommand(Command):
    """Send a greeting to a user."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing GreetingCommand implementation with context: {context}")
        if context and "user_id" in context:
            return CommandResponse.success(f"Hello <@{context['user_id']}>!")
        return CommandResponse.success("Hello there!")


class EchoCommand(Command):
    """Echo back the input text.
    
    Usage: echo <text>
    """
    
    def __init__(self):
        super().__init__()
        # Explicitly indicate that this command accepts arbitrary arguments
        self.accepts_arguments = True
    
    def _execute_impl(self, context):
        logger.debug(f"Executing EchoCommand implementation with context: {context}")
        logger.debug(f"EchoCommand class: {self.__class__.__name__}")
        logger.debug(f"EchoCommand has _execute_impl: {hasattr(self, '_execute_impl')}")
        
        if not context:
            logger.debug("No context provided to EchoCommand")
            return CommandResponse.error("No context provided")
            
        # Try to get text from tokens
        if "tokens" in context and context["tokens"]:
            text_to_echo = " ".join(context["tokens"])
            logger.debug(f"Found tokens in context: {context['tokens']}")
            logger.debug(f"Echoing text: '{text_to_echo}'")
            return CommandResponse.success(f"Echo: {text_to_echo}", ephemeral=False)
        
        # No text to echo
        logger.debug("No text to echo found, returning error")
        return CommandResponse.error("Please provide some text to echo. Usage: echo <text>")


class WeatherCommand(Command):
    """Get the weather information."""
    
    def __init__(self):
        super().__init__()
        # Register subcommands
        self.register_subcommand("today", TodayWeatherCommand())
        self.register_subcommand("forecast", ForecastWeatherCommand())
        # Command with subcommands doesn't accept arbitrary arguments (this is already the default)
        self.accepts_arguments = False
        logger.debug("WeatherCommand initialized with subcommands")
    
    def _execute_impl(self, context):
        logger.debug(f"Executing WeatherCommand implementation with context: {context}")
        # Default to showing help
        return self.show_help()


class TodayWeatherCommand(Command):
    """Get today's weather."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing TodayWeatherCommand implementation with context: {context}")
        return CommandResponse.success("Today's weather: Sunny and 75°F")


class ForecastWeatherCommand(Command):
    """Get the weather forecast."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing ForecastWeatherCommand implementation with context: {context}")
        forecast = [
            "Today: Sunny and 75°F",
            "Tomorrow: Partly cloudy and 72°F",
            "Wednesday: Rainy and 65°F"
        ]
        return CommandResponse("\n".join(forecast), ephemeral=False)


def setup_demo_app():
    """Set up and configure the demo Slack app."""
    logger.debug("Setting up demo Slack app")
    
    # Initialize the Slack Bolt app
    logger.debug("Initializing Slack Bolt app")
    app = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
    )
    
    # Create command registry
    logger.debug("Creating command registry")
    registry = CommandRegistry()
    
    # Register commands
    logger.info("Registering commands...")
    registry.register_command("greet", GreetingCommand())
    registry.register_command("echo", EchoCommand())
    registry.register_command("weather", WeatherCommand())
    logger.debug("Registered commands: greet, echo, weather")
    
    # Handle the slash command
    @app.command("/demo")
    def handle_demo_command(ack, command, say):
        # Acknowledge receipt of the command
        ack()
        
        logger.info(f"Received command: {command['text']}")
        logger.debug(f"Full command payload: {command}")
        
        # Parse command text to extract tokens
        text = command["text"].strip() if command.get("text") else ""
        
        # Create context object with command information
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        try:
            # Route the command - the registry will handle token extraction
            logger.debug(f"Routing command: '{text}'")
            result = registry.route_command(text, context)
            logger.debug(f"Command result: {result.__dict__}")
            
            # Send the response
            logger.debug(f"Sending response: {result.as_dict()}")
            say(**result.as_dict())
            
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}", exc_info=True)
            say(text=f"An error occurred: {str(e)}")
    
    logger.debug("Slack Bolt app setup complete")
    return app


def main():
    """Main entry point for the demo app."""
    logger.info("Starting Phase 4 Demo: Server Integration with Slack Bolt")
    
    app = setup_demo_app()
    
    # Check if we have the required tokens
    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    if not slack_app_token:
        logger.warning("SLACK_APP_TOKEN not found in environment variables")
        logger.info("For a real demo, please set up the .env file with your Slack credentials")
        logger.info("Exiting demo - set up your .env file and try again")
        return
    
    # Log token information securely (only first few chars)
    if slack_app_token:
        logger.debug(f"Using app token: {slack_app_token[:10]}***")
    
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if bot_token:
        logger.debug(f"Using bot token: {bot_token[:10]}***")
    
    logger.info("Starting Slack app in Socket Mode")
    handler = SocketModeHandler(app, slack_app_token)
    
    try:
        handler.start()
    except Exception as e:
        logger.error(f"Error starting Socket Mode handler: {str(e)}", exc_info=True)
        logger.info("Please check your Slack API credentials")


if __name__ == "__main__":
    main() 