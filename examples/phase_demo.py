#!/usr/bin/env python3
"""
Progressive demo of the Slack Commands Library.

This script progressively demonstrates the features implemented in:
- Phase 1: Core Command and Response Structure
- Phase 2: Command Registry and Routing
- Phase 3: Help System Implementation
- Phase 4: Server Integration with Slack Bolt
"""

import time
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.registry import CommandRegistry


def separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def phase1_demo():
    """Demonstrate Phase 1: Core Command and Response Structure."""
    separator("PHASE 1: CORE COMMAND AND RESPONSE STRUCTURE")
    print("Creating and executing basic commands...\n")
    
    # Create a basic command
    command = Command()
    command._set_name("test")
    response = command.execute()
    print("Basic command response:")
    print(response.as_dict())
    
    # Create a custom command
    class HelloCommand(Command):
        """Say hello to a user."""
        
        def execute(self, context=None):
            return CommandResponse.success("Hello, world!")
    
    hello_cmd = HelloCommand()
    hello_cmd._set_name("hello")
    response = hello_cmd.execute()
    print("\nCustom command response:")
    print(response.as_dict())
    
    # Demonstrate different response types
    print("\nDifferent response types:")
    print("Error response:", CommandResponse.error("Something went wrong").as_dict())
    print("Success response (private):", CommandResponse.success("Operation completed").as_dict())
    print("Success response (public):", CommandResponse.success("Announcement to channel", ephemeral=False).as_dict())
    
    # Return the HelloCommand for use in phase 2
    return HelloCommand


def phase2_demo(HelloCommand):
    """Demonstrate Phase 2: Command Registry and Routing."""
    separator("PHASE 2: COMMAND REGISTRY AND ROUTING")
    
    # Create a registry
    print("Creating command registry...\n")
    registry = CommandRegistry()
    
    # Register top-level command
    print("Registering commands and subcommands...\n")
    hello_cmd = registry.register_command("hello", HelloCommand())
    
    # Register subcommand
    class WorldCommand(Command):
        """Show a greeting to the world."""
        
        def execute(self, context=None):
            return CommandResponse.success("Hello, world!", ephemeral=False)
    
    hello_cmd.register_subcommand("world", WorldCommand())
    
    # Create another command for more complex demos
    class UserCommand(Command):
        """Manage users in the system."""
        
        def execute(self, context=None):
            # Default to showing help
            return self.show_help()
    
    user_cmd = registry.register_command("user", UserCommand())
    
    class ListUsersCommand(Command):
        """List all users in the system."""
        
        def execute(self, context=None):
            return CommandResponse("User list: Alice, Bob, Charlie")
    
    user_cmd.register_subcommand("list", ListUsersCommand())
    
    # Test routing top-level commands
    print("Testing command routing...\n")
    
    response = registry.route_command("hello", {})
    print("Route 'hello':", response.as_dict())
    
    response = registry.route_command("hello world", {})
    print("Route 'hello world':", response.as_dict())
    
    response = registry.route_command("unknown", {})
    print("Route 'unknown':", response.as_dict())
    
    # Test help functionality
    print("\nTesting help functionality...\n")
    
    response = registry.route_command("help", {})
    print("Route 'help' (top-level):", response.as_dict())
    
    response = registry.route_command("hello help", {})
    print("Route 'hello help':", response.as_dict())
    
    response = registry.route_command("user help", {})
    print("Route 'user help':", response.as_dict())
    
    response = registry.route_command("user list help", {})
    print("Route 'user list help':", response.as_dict())
    
    # Test overriding help
    print("\nTesting help text override...\n")
    
    list_cmd = user_cmd.subcommands["list"]
    list_cmd.set_help("List all users", "Display a comprehensive list of all users in the system in a formatted output.")
    
    response = registry.route_command("user list help", {})
    print("Route 'user list help' (with override):", response.as_dict())
    
    # Return the registry and commands for phase 3
    return registry, user_cmd, list_cmd


def phase3_demo(registry, user_cmd, list_cmd):
    """Demonstrate Phase 3: Help System Implementation."""
    separator("PHASE 3: HELP SYSTEM IMPLEMENTATION")
    
    print("Enhancing commands with usage examples...\n")
    
    # Add usage example to a command
    list_cmd.set_help(
        short_help="List all users",
        long_help="Display a comprehensive list of all users in the system in a formatted output.",
        usage_example="user list [--filter=active]"
    )
    
    # Test help with usage example
    response = registry.route_command("user list help", {})
    print("Help with usage example:", response.as_dict())
    
    print("\nDemonstrating Block Kit formatted help...\n")
    
    # Create a new command with Block Kit formatting
    class ConfigCommand(Command):
        """Manage system configuration.
        
        This command allows you to view and modify system configuration settings.
        You can list all settings, get specific settings, or update settings.
        """
        
        def __init__(self):
            super().__init__()
            self.use_block_kit = True
    
    config_cmd = registry.register_command("config", ConfigCommand())
    
    class GetConfigCommand(Command):
        """Get the value of a configuration setting."""
        
        def __init__(self):
            super().__init__()
            self.use_block_kit = True
            self.set_help(
                usage_example="config get <setting_name>"
            )
        
        def execute(self, context=None):
            return CommandResponse("Configuration setting value would be displayed here")
    
    config_cmd.register_subcommand("get", GetConfigCommand())
    
    class SetConfigCommand(Command):
        """Set a configuration setting value."""
        
        def __init__(self):
            super().__init__()
            self.use_block_kit = True
            self.set_help(
                usage_example="config set <setting_name> <value>"
            )
        
        def execute(self, context=None):
            return CommandResponse.success("Configuration setting updated")
    
    config_cmd.register_subcommand("set", SetConfigCommand())
    
    # Test Block Kit formatted help
    response = registry.route_command("config help", {})
    print("Block Kit formatted help:")
    
    # Print each block for clarity
    blocks = response.content
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(block)
    
    # Create a registry with Block Kit top-level help
    print("\nDemonstrating Block Kit formatted top-level help...\n")
    block_kit_registry = CommandRegistry(help_format="block_kit")
    
    # Register some commands
    block_kit_registry.register_command("hello", HelloCommand())
    block_kit_registry.register_command("config", ConfigCommand())
    
    # Get top-level help
    response = block_kit_registry.route_command("help", {})
    print("Block Kit top-level help:")
    
    blocks = response.content
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(block)
    
    # Return registry for phase 4
    return registry


def phase4_demo(registry):
    """Demonstrate Phase 4: Server Integration with Slack Bolt."""
    separator("PHASE 4: SERVER INTEGRATION WITH SLACK BOLT")
    
    print("Setting up a Slack Bolt app for slash commands...\n")
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    missing_vars = []
    if not os.environ.get("SLACK_BOT_TOKEN"):
        missing_vars.append("SLACK_BOT_TOKEN")
    if not os.environ.get("SLACK_SIGNING_SECRET"):
        missing_vars.append("SLACK_SIGNING_SECRET")
    
    if missing_vars:
        print("Required environment variables for actual Slack integration are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nFor a complete demo, set these variables in your .env file.")
        print("Showing simulation of server integration instead...\n")
        
        # Create a simulated server demo
        simulate_slack_integration(registry)
        return
    
    # Add weather commands for the demo
    class WeatherCommand(Command):
        """Get weather information."""
        
        def __init__(self):
            super().__init__()
            # Register subcommands
            self.register_subcommand("today", TodayWeatherCommand())
            self.register_subcommand("forecast", ForecastWeatherCommand())
        
        def execute(self, context=None):
            # Default to showing help
            return self.show_help()
    
    class TodayWeatherCommand(Command):
        """Get today's weather."""
        
        def execute(self, context=None):
            return CommandResponse.success("Today's weather: Sunny and 75°F")
    
    class ForecastWeatherCommand(Command):
        """Get the weather forecast."""
        
        def execute(self, context=None):
            forecast = [
                "Today: Sunny and 75°F",
                "Tomorrow: Partly cloudy and 72°F",
                "Wednesday: Rainy and 65°F"
            ]
            return CommandResponse("\n".join(forecast), ephemeral=False)
    
    # Add echo command
    class EchoCommand(Command):
        """Echo back the input text."""
        
        def execute(self, context=None):
            if not context:
                return CommandResponse.error("No context provided")
                
            # Check if we have tokens in the context
            if "tokens" in context and context["tokens"]:
                text_to_echo = " ".join(context["tokens"])
                return CommandResponse.success(f"Echo: {text_to_echo}", ephemeral=False)
            
            # Otherwise return an error
            return CommandResponse.error("Please provide some text to echo. Usage: echo <text>")
    
    registry.register_command("weather", WeatherCommand())
    registry.register_command("echo", EchoCommand())
    
    # Initialize the Slack Bolt app
    app = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
    )
    
    # Handle the slash command
    @app.command("/demo")
    def handle_demo_command(ack, command, say):
        # Acknowledge receipt of the command
        ack()
        
        print(f"Received command: {command['text']}")
        
        # Create context from command
        context = {
            "user_id": command["user_id"],
            "channel_id": command["channel_id"],
            "team_id": command["team_id"],
            "command": command
        }
        
        try:
            # Parse command text and route the command
            text = command["text"].strip() if command.get("text") else ""
            result = registry.route_command(text, context)
            
            # Send the response
            say(**result.as_dict())
            
        except Exception as e:
            print(f"Error: {str(e)}")
            say(text=f"An error occurred: {str(e)}")
    
    print("Slack Bolt app is configured and ready!")
    print()
    print("Available commands:")
    print("  /demo help               - Show help for all commands")
    print("  /demo hello              - Get a greeting")
    print("  /demo hello world        - Get a greeting to the world")
    print("  /demo user               - Show user commands help")
    print("  /demo user list          - List users")
    print("  /demo config             - Show config commands help")
    print("  /demo echo <text>        - Echo back your text")
    print("  /demo weather            - Show weather commands help")
    print("  /demo weather today      - Get today's weather")
    print("  /demo weather forecast   - Get the weather forecast")
    print()
    
    print("Note: In a real implementation, you would now start the Slack app with:")
    print("  app.start(port=3000)  # For HTTP mode")
    print("  # or")
    print("  handler = SocketModeHandler(app, os.environ.get('SLACK_APP_TOKEN'))")
    print("  handler.start()  # For Socket Mode")
    print("\nThis demo stops here to avoid actually starting a server.")


def simulate_slack_integration(registry):
    """Simulate Slack slash command interactions."""
    print("Simulating Slack slash command interactions...\n")
    
    # Add the echo command to the registry
    # Add echo command
    class EchoCommand(Command):
        """Echo back the input text."""
        
        def execute(self, context=None):
            if not context:
                return CommandResponse.error("No context provided")
                
            # Check if we have tokens in the context
            if "tokens" in context and context["tokens"]:
                text_to_echo = " ".join(context["tokens"])
                return CommandResponse.success(f"Echo: {text_to_echo}", ephemeral=False)
            
            # Otherwise return an error
            return CommandResponse.error("Please provide some text to echo. Usage: echo <text>")
    
    registry.register_command("echo", EchoCommand())
    
    # Simulate a few commands
    simulate_command("/demo help", registry)
    simulate_command("/demo hello", registry)
    simulate_command("/demo echo Hello world!", registry)
    simulate_command("/demo unknown", registry)
    simulate_command("/demo config get api_key", registry)


def simulate_command(command_str, registry):
    """Simulate processing a slash command."""
    # Split into command name and text
    parts = command_str.split(maxsplit=1)
    command_name = parts[0] if parts else ""
    command_text = parts[1] if len(parts) > 1 else ""
    
    print(f"User enters: {command_str}")
    
    # Create a simulated command object
    command = {
        "command": command_name,
        "text": command_text,
        "user_id": "U12345678",
        "channel_id": "C87654321",
        "team_id": "T11223344",
    }
    
    # Create context for the command
    context = {
        "user_id": command["user_id"],
        "channel_id": command["channel_id"],
        "team_id": command["team_id"],
        "command": command
    }
    
    print("Slack acknowledges command receipt...")
    
    try:
        # Route the command - registry will handle token extraction
        result = registry.route_command(command_text, context)
        
        # Print the response that would be sent to Slack
        print("Response to Slack:")
        print(f"  {result.as_dict()}\n")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}\n")


if __name__ == "__main__":
    print("PROGRESSIVE DEMO OF SLACK COMMANDS LIBRARY")
    print("This demonstrates the features implemented in Phases 1, 2, 3, and 4")
    
    # Run Phase 1 demo
    HelloCommand = phase1_demo()
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 2 demo
    registry, user_cmd, list_cmd = phase2_demo(HelloCommand)
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 3 demo
    registry = phase3_demo(registry, user_cmd, list_cmd)
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 4 demo
    phase4_demo(registry) 