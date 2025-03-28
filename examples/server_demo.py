#!/usr/bin/env python3
"""
Demo: Server Integration with Slack Bolt.

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
   python examples/server_demo.py
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
from slackcmds.core.validation import (
    Parameter, ParameterType, min_length, max_length, 
    min_value, max_value, pattern, register_parameter_type, register_validator
)
from slackcmds.core import block_kit

# Load environment variables first so we can use them for logging
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("server_demo")

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


# ======================================================
# Phase 5 Commands - Input Validation Framework
# ======================================================

class UserCommand(Command):
    """Manage users in the system."""
    
    def __init__(self):
        super().__init__()
        # Register subcommands
        self.register_subcommand("add", AddUserCommand())
        self.register_subcommand("search", SearchUserCommand())
        logger.debug("UserCommand initialized with subcommands")
    
    def _execute_impl(self, context):
        logger.debug(f"Executing UserCommand implementation with context: {context}")
        # Default to showing help
        return self.show_help()


class AddUserCommand(Command):
    """Add a new user to the system.
    
    Usage: user add <username> <email> [role]
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters with validation rules
        self.add_parameters([
            Parameter("username", "string", required=True, 
                      validators=[min_length(3), max_length(20)],
                      help_text="Username (3-20 characters)"),
            Parameter("email", "email", required=True,
                      help_text="Valid email address"),
            Parameter("role", "choice", required=False,
                      choices=["admin", "user", "guest"], default="user",
                      help_text="User role (default: user)")
        ])
        logger.debug("AddUserCommand initialized with parameter validation")
    
    def _execute_impl(self, context):
        logger.debug(f"Executing AddUserCommand with context: {context}")
        
        # Access validated parameters from context
        params = context["validated_params"]
        username = params["username"]
        email = params["email"]
        role = params["role"]
        
        logger.info(f"Adding user: {username} ({email}) with role {role}")
        
        # In a real application, this would add the user to a database
        return CommandResponse.success(
            f"Added user {username} with email {email} and role {role}",
            ephemeral=False
        )


class SearchUserCommand(Command):
    """Search for users by various criteria.
    
    Usage: user search <query> [limit]
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters with validation rules
        self.add_parameters([
            Parameter("query", "string", required=True,
                      validators=[min_length(2)],
                      help_text="Search query (min 2 characters)"),
            Parameter("limit", "integer", required=False, 
                      default=10, validators=[min_value(1), max_value(100)],
                      help_text="Maximum results to return (1-100, default: 10)")
        ])
        logger.debug("SearchUserCommand initialized with parameter validation")
    
    def _execute_impl(self, context):
        logger.debug(f"Executing SearchUserCommand with context: {context}")
        
        # Access validated parameters from context
        params = context["validated_params"]
        query = params["query"]
        limit = params["limit"]
        
        # In a real application, this would search a database
        # Just mock some results for the demo
        mock_results = [
            {"username": "john_doe", "email": "john@example.com", "role": "admin"},
            {"username": "jane_smith", "email": "jane@example.com", "role": "user"},
            {"username": "alice_jones", "email": "alice@example.com", "role": "user"}
        ]
        
        # Filter based on query (simple case-insensitive contains)
        filtered_results = [
            user for user in mock_results 
            if query.lower() in user["username"].lower() or query.lower() in user["email"].lower()
        ]
        
        # Apply limit
        limited_results = filtered_results[:limit]
        
        if not limited_results:
            return CommandResponse.error(f"No users found matching '{query}'")
        
        # Format results
        result_text = f"Found {len(limited_results)} users matching '{query}':\n\n"
        for user in limited_results:
            result_text += f"• *{user['username']}* - {user['email']} (role: {user['role']})\n"
        
        return CommandResponse(result_text)


class CalculatorCommand(Command):
    """Perform a calculation.
    
    Usage: calc <operation> <number1> <number2>
    """
    
    def __init__(self):
        super().__init__()
        # Register subcommands
        self.register_subcommand("add", AddNumbersCommand())
        self.register_subcommand("subtract", SubtractNumbersCommand())
        self.register_subcommand("multiply", MultiplyNumbersCommand())
        self.register_subcommand("divide", DivideNumbersCommand())
        logger.debug("CalculatorCommand initialized with subcommands")
    
    def _execute_impl(self, context):
        logger.debug(f"Executing CalculatorCommand implementation with context: {context}")
        # Default to showing help
        return self.show_help()


class AddNumbersCommand(Command):
    """Add two numbers.
    
    Usage: calc add <number1> <number2>
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters
        self.add_parameters([
            Parameter("number1", "float", required=True,
                      help_text="First number"),
            Parameter("number2", "float", required=True,
                      help_text="Second number")
        ])
    
    def _execute_impl(self, context):
        logger.debug(f"Executing AddNumbersCommand with context: {context}")
        
        # Access validated parameters
        params = context["validated_params"]
        num1 = params["number1"]
        num2 = params["number2"]
        
        result = num1 + num2
        return CommandResponse.success(f"{num1} + {num2} = {result}")


class SubtractNumbersCommand(Command):
    """Subtract the second number from the first.
    
    Usage: calc subtract <number1> <number2>
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters
        self.add_parameters([
            Parameter("number1", "float", required=True,
                      help_text="First number"),
            Parameter("number2", "float", required=True,
                      help_text="Second number")
        ])
    
    def _execute_impl(self, context):
        logger.debug(f"Executing SubtractNumbersCommand with context: {context}")
        
        # Access validated parameters
        params = context["validated_params"]
        num1 = params["number1"]
        num2 = params["number2"]
        
        result = num1 - num2
        return CommandResponse.success(f"{num1} - {num2} = {result}")


class MultiplyNumbersCommand(Command):
    """Multiply two numbers.
    
    Usage: calc multiply <number1> <number2>
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters
        self.add_parameters([
            Parameter("number1", "float", required=True,
                      help_text="First number"),
            Parameter("number2", "float", required=True,
                      help_text="Second number")
        ])
    
    def _execute_impl(self, context):
        logger.debug(f"Executing MultiplyNumbersCommand with context: {context}")
        
        # Access validated parameters
        params = context["validated_params"]
        num1 = params["number1"]
        num2 = params["number2"]
        
        result = num1 * num2
        return CommandResponse.success(f"{num1} × {num2} = {result}")


class DivideNumbersCommand(Command):
    """Divide the first number by the second.
    
    Usage: calc divide <number1> <number2>
    """
    
    def __init__(self):
        super().__init__()
        # Define expected parameters with validation
        self.add_parameters([
            Parameter("number1", "float", required=True,
                      help_text="First number (dividend)"),
            Parameter("number2", "float", required=True,
                      help_text="Second number (divisor, cannot be zero)")
        ])
    
    def validate(self, context=None):
        # First, perform standard parameter validation
        result = super().validate(context)
        if not result.success:
            return result
        
        # Additional custom validation: Check for division by zero
        if context and "tokens" in context and len(context["tokens"]) >= 2:
            try:
                divisor = float(context["tokens"][1])
                if divisor == 0:
                    return CommandResponse.error("Cannot divide by zero")
            except (ValueError, IndexError):
                # Let the standard validation handle this
                pass
        
        return result
    
    def _execute_impl(self, context):
        logger.debug(f"Executing DivideNumbersCommand with context: {context}")
        
        # Access validated parameters
        params = context["validated_params"]
        num1 = params["number1"]
        num2 = params["number2"]
        
        result = num1 / num2
        return CommandResponse.success(f"{num1} ÷ {num2} = {result}")


# ======================================================
# Custom Validator Example
# ======================================================

from slackcmds.core.validation import register_parameter_type, register_validator
import re

# Register a custom validator for Twitter/X handles
def twitter_handle(value):
    """Validate that a string is a valid Twitter/X handle.
    
    Args:
        value: The string to validate
        
    Returns:
        None if valid, error message if invalid
    """
    if not value.startswith('@'):
        return "Twitter handle must start with @"
    
    # Remove @ symbol for further validation
    handle = value[1:]
    
    if len(handle) < 4:
        return "Twitter handle must be at least 4 characters (not including @)"
    
    if len(handle) > 15:
        return "Twitter handle cannot exceed 15 characters (not including @)"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', handle):
        return "Twitter handle can only contain letters, numbers, and underscores"
    
    return None

# Register the validator
register_validator("twitter_handle", twitter_handle)

# Register a custom parameter type for Twitter handles
def validate_twitter_handle(value):
    """Validate and process a Twitter handle.
    
    Args:
        value: The string to validate
        
    Returns:
        Tuple of (validated_value, error_message)
    """
    # If handle doesn't start with @, add it
    if not value.startswith('@'):
        value = '@' + value
    
    # Apply our validator
    error = twitter_handle(value)
    if error:
        return None, error
    
    return value, None

# Register the parameter type
register_parameter_type(
    "twitter_handle",
    "Twitter/X username (e.g. @username)",
    validate_twitter_handle
)

# Example command that uses our custom validator and parameter type
class SocialProfileCommand(Command):
    """Set your social media profiles.
    
    Usage: social twitter <handle>
    """
    
    def __init__(self):
        super().__init__()
        # Use our custom parameter type
        self.add_parameter(
            Parameter("handle", "twitter_handle", required=True,
                      help_text="Your Twitter/X handle (e.g. @username)")
        )
    
    def _execute_impl(self, context):
        logger.debug(f"Executing SocialProfileCommand with context: {context}")
        
        # Access validated parameters
        params = context["validated_params"]
        handle = params["handle"]
        
        return CommandResponse.success(f"Twitter profile set to {handle}")


# ======================================================
# Phase 6 Commands - Block Kit Response Formatting
# ======================================================

class StatusCommand(Command):
    """Show the system status with rich formatting."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing StatusCommand with context: {context}")
        
        # Create blocks using Block Kit helpers
        blocks = [
            block_kit.header("System Status"),
            block_kit.divider(),
            block_kit.section("System Components", fields=[
                "*Database:*\n:white_check_mark: Online",
                "*API:*\n:white_check_mark: Operational",
                "*Web Server:*\n:white_check_mark: Running"
            ]),
            block_kit.divider(),
            block_kit.context(["Last updated: just now"])
        ]
        
        return CommandResponse.with_blocks(blocks, ephemeral=False)


class UserProfileCommand(Command):
    """Display user profile information using Block Kit formatting."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing UserProfileCommand with context: {context}")
        
        # Get user ID from context
        user_id = context.get("user_id", "Unknown User")
        
        # Use CommandResponse.information helper method
        user_details = [
            f"*User:* <@{user_id}>",
            "*Account Type:* Premium",
            "*Status:* Active",
            "*Member Since:* January 2023"
        ]
        
        return CommandResponse.information(
            "User Profile", 
            user_details,
            ephemeral=True
        )


class PermissionsCommand(Command):
    """List permissions in a table format."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing PermissionsCommand with context: {context}")
        
        # Use the table helper method
        headers = ["Permission", "Description", "Default Role"]
        rows = [
            ["read", "Can read content", "Everyone"],
            ["write", "Can create and edit content", "Editors"],
            ["delete", "Can remove content", "Admins"],
            ["admin", "Full system access", "Owners"]
        ]
        
        return CommandResponse.table(
            "System Permissions",
            headers,
            rows,
            ephemeral=True
        )


class ConfirmCommand(Command):
    """Show a confirmation dialog with interactive buttons."""
    
    def __init__(self):
        super().__init__()
        self.register_subcommand("delete", ConfirmDeleteCommand())
        self.register_subcommand("publish", ConfirmPublishCommand())
    
    def _execute_impl(self, context):
        logger.debug(f"Executing ConfirmCommand with context: {context}")
        return self.show_help()


class ConfirmDeleteCommand(Command):
    """Show a confirmation dialog for deletion."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing ConfirmDeleteCommand with context: {context}")
        
        # Create buttons using block_kit helpers
        choices = [
            block_kit.button("Yes, Delete", "confirm_delete", style="danger"),
            block_kit.button("Cancel", "cancel_delete")
        ]
        
        return CommandResponse.confirmation(
            "Confirm Deletion",
            "Are you sure you want to delete this item? This action cannot be undone.",
            choices,
            ephemeral=True
        )


class ConfirmPublishCommand(Command):
    """Show a confirmation dialog for publishing."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing ConfirmPublishCommand with context: {context}")
        
        # Create buttons using block_kit helpers
        choices = [
            block_kit.button("Publish Now", "publish_now", style="primary"),
            block_kit.button("Schedule", "schedule_publish"),
            block_kit.button("Cancel", "cancel_publish")
        ]
        
        return CommandResponse.confirmation(
            "Publish Content",
            "How would you like to publish this content?",
            choices,
            ephemeral=True
        )


class FormCommand(Command):
    """Show a form for collecting information."""
    
    def __init__(self):
        super().__init__()
        self.register_subcommand("event", EventFormCommand())
        self.register_subcommand("feedback", FeedbackFormCommand())
    
    def _execute_impl(self, context):
        logger.debug(f"Executing FormCommand with context: {context}")
        return self.show_help()


class EventFormCommand(Command):
    """Show a form for creating an event."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing EventFormCommand with context: {context}")
        
        # Create input elements for the form
        input_elements = [
            block_kit.input_block(
                "Event Name",
                block_kit.plain_text_input("event_name", placeholder="Enter event name")
            ),
            block_kit.input_block(
                "Date",
                block_kit.plain_text_input("event_date", placeholder="YYYY-MM-DD")
            ),
            block_kit.input_block(
                "Description",
                block_kit.plain_text_input("event_description", placeholder="Enter event description", multiline=True),
                optional=True
            ),
            block_kit.input_block(
                "Event Type",
                block_kit.select_menu(
                    "Select event type",
                    "event_type",
                    [
                        block_kit.option("Meeting", "meeting"),
                        block_kit.option("Conference", "conference"),
                        block_kit.option("Workshop", "workshop"),
                        block_kit.option("Other", "other")
                    ]
                )
            )
        ]
        
        return CommandResponse.form(
            "Create New Event",
            input_elements,
            submit_label="Create Event",
            ephemeral=True
        )


class FeedbackFormCommand(Command):
    """Show a form for submitting feedback."""
    
    def _execute_impl(self, context):
        logger.debug(f"Executing FeedbackFormCommand with context: {context}")
        
        # Create input elements for the form
        input_elements = [
            block_kit.input_block(
                "Rating",
                block_kit.select_menu(
                    "How would you rate your experience?",
                    "rating",
                    [
                        block_kit.option("Excellent", "5"),
                        block_kit.option("Good", "4"),
                        block_kit.option("Average", "3"),
                        block_kit.option("Below Average", "2"),
                        block_kit.option("Poor", "1")
                    ]
                )
            ),
            block_kit.input_block(
                "Feedback",
                block_kit.plain_text_input(
                    "feedback_text", 
                    placeholder="Please share your thoughts...",
                    multiline=True
                )
            ),
            block_kit.input_block(
                "Name",
                block_kit.plain_text_input("name", placeholder="Your name (optional)"),
                optional=True
            )
        ]
        
        return CommandResponse.form(
            "Submit Feedback",
            input_elements,
            submit_label="Submit",
            ephemeral=True
        )


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
    
    # Register Phase 4 commands (existing)
    logger.info("Registering Phase 4 commands...")
    registry.register_command("greet", GreetingCommand())
    registry.register_command("echo", EchoCommand())
    registry.register_command("weather", WeatherCommand())
    logger.debug("Registered commands: greet, echo, weather")
    
    # Register Phase 5 commands (with validation)
    logger.info("Registering Phase 5 commands with validation...")
    registry.register_command("user", UserCommand())
    registry.register_command("calc", CalculatorCommand())
    
    # Register our custom validator example command
    social_cmd = Command()
    social_cmd.register_subcommand("twitter", SocialProfileCommand())
    registry.register_command("social", social_cmd)
    
    logger.debug("Registered commands: user, calc, social")
    
    # Register Phase 6 commands (with Block Kit formatting)
    logger.info("Registering Phase 6 commands with Block Kit formatting...")
    registry.register_command("status", StatusCommand())
    registry.register_command("profile", UserProfileCommand())
    registry.register_command("permissions", PermissionsCommand())
    registry.register_command("confirm", ConfirmCommand())
    registry.register_command("form", FormCommand())
    
    logger.debug("Registered Block Kit commands: status, profile, permissions, confirm, form")
    
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
    logger.info("Demo Server: Integration with Slack Bolt")
    
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