#!/usr/bin/env python3
"""
Progressive demo of the Slack Commands Library.

This script progressively demonstrates the features implemented in:
- Phase 1: Core Command and Response Structure
- Phase 2: Command Registry and Routing
- Phase 3: Help System Implementation
- Phase 4: Server Integration with Slack Bolt
- Phase 5: Input Validation Framework
- Phase 6: Block Kit Response Formatting
"""

import time
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.validation import Parameter, ParameterType, min_length, min_value, max_value
from slackcmds.core import block_kit


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


def phase5_demo(registry):
    """Demonstrate Phase 5: Input Validation Framework."""
    separator("PHASE 5: INPUT VALIDATION FRAMEWORK")
    
    print("Demonstrating command parameter validation...\n")
    
    # Create a command that requires validated parameters
    class AddUserCommand(Command):
        """Add a new user to the system.
        
        Usage: user add <username> <email> [role]
        """
        
        def __init__(self):
            super().__init__()
            # Define expected parameters
            self.add_parameters([
                Parameter("username", ParameterType.STRING, required=True, 
                          validators=[min_length(3)],
                          help_text="Username (min 3 characters)"),
                Parameter("email", ParameterType.EMAIL, required=True,
                          help_text="Valid email address"),
                Parameter("role", ParameterType.CHOICE, required=False,
                          choices=["admin", "user", "guest"], default="user",
                          help_text="User role (default: user)")
            ])
        
        def _execute_impl(self, context):
            # Access validated parameters
            params = context["validated_params"]
            username = params["username"]
            email = params["email"]
            role = params["role"]
            
            return CommandResponse.success(
                f"Added user {username} with email {email} and role {role}",
                ephemeral=False
            )
    
    # Create a command with numeric validation
    class SetLimitCommand(Command):
        """Set a numeric limit.
        
        Usage: config set-limit <value>
        """
        
        def __init__(self):
            super().__init__()
            self.add_parameter(
                Parameter("value", ParameterType.INTEGER, required=True,
                          validators=[min_value(1), max_value(100)],
                          help_text="Limit value (1-100)")
            )
        
        def _execute_impl(self, context):
            value = context["validated_params"]["value"]
            return CommandResponse.success(f"Limit set to {value}")
    
    # Register commands
    user_cmd = registry.register_command("user", Command())
    user_cmd.register_subcommand("add", AddUserCommand())
    
    config_cmd = registry.register_command("config", Command())
    config_cmd.register_subcommand("set-limit", SetLimitCommand())
    
    # Test with valid parameters
    print("Testing valid parameters...")
    context = {"tokens": ["john", "john@example.com", "admin"]}
    response = registry.route_command("user add", context)
    print(f"Command 'user add' with valid parameters: {response.as_dict()}")
    
    # Test with invalid parameters
    print("\nTesting invalid parameters...")
    
    # Missing required parameter
    context = {"tokens": ["jo"]}
    response = registry.route_command("user add", context)
    print("\nMissing and too short username:")
    print(response.as_dict())
    
    # Invalid email
    context = {"tokens": ["john", "not-an-email"]}
    response = registry.route_command("user add", context)
    print("\nInvalid email:")
    print(response.as_dict())
    
    # Invalid role choice
    context = {"tokens": ["john", "john@example.com", "superuser"]}
    response = registry.route_command("user add", context)
    print("\nInvalid role choice:")
    print(response.as_dict())
    
    # Test numeric validation
    print("\nTesting numeric validation...")
    
    # Valid number
    context = {"tokens": ["50"]}
    response = registry.route_command("config set-limit", context)
    print("\nValid limit value:")
    print(response.as_dict())
    
    # Number out of range
    context = {"tokens": ["150"]}
    response = registry.route_command("config set-limit", context)
    print("\nLimit value out of range:")
    print(response.as_dict())
    
    # Not a number
    context = {"tokens": ["not-a-number"]}
    response = registry.route_command("config set-limit", context)
    print("\nInvalid numeric value:")
    print(response.as_dict())
    
    print("\nParameter validation framework demonstration complete!")
    
    return registry


def phase6_demo(registry):
    """Demonstrate Phase 6: Block Kit Response Formatting."""
    separator("PHASE 6: BLOCK KIT RESPONSE FORMATTING")
    
    print("Demonstrating Block Kit response formatting...\n")
    
    # Create commands that utilize Block Kit formatting
    class StatusCommand(Command):
        """Show system status with rich formatting."""
        
        def execute(self, context=None):
            # Use the block_kit module to create blocks
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
    
    # Register the command
    registry.register_command("status", StatusCommand())
    
    # Create a command using the pre-built Block Kit response methods
    class UserProfileCommand(Command):
        """Display user profile information."""
        
        def execute(self, context=None):
            # Use CommandResponse.information helper method
            user_details = [
                "*Name:* John Doe",
                "*Email:* john@example.com",
                "*Role:* Administrator",
                "*Status:* Active"
            ]
            
            return CommandResponse.information(
                "User Profile", 
                user_details,
                ephemeral=False
            )
    
    # Create a command for tabular data
    class ListPermissionsCommand(Command):
        """List permissions in a table format."""
        
        def execute(self, context=None):
            # Use CommandResponse.table helper
            headers = ["Permission", "Description", "Default"]
            rows = [
                ["read", "Can read documents", "All users"],
                ["write", "Can create and edit documents", "Editors"],
                ["admin", "Full system access", "Administrators"]
            ]
            
            return CommandResponse.table(
                "System Permissions",
                headers,
                rows,
                ephemeral=False
            )
    
    # Create a command with interactive buttons
    class ConfirmActionCommand(Command):
        """Demonstrate an action confirmation dialog."""
        
        def execute(self, context=None):
            # Create buttons using block_kit helpers
            choices = [
                block_kit.button("Approve", "approve_action", style="primary"),
                block_kit.button("Reject", "reject_action", style="danger")
            ]
            
            return CommandResponse.confirmation(
                "Confirm Action",
                "Are you sure you want to proceed with this action?",
                choices,
                ephemeral=True
            )
    
    # Create a command that displays a form
    class CreateItemCommand(Command):
        """Show a form for creating a new item."""
        
        def execute(self, context=None):
            # Create input elements
            input_elements = [
                block_kit.input_block(
                    "Item Name",
                    block_kit.plain_text_input("item_name", placeholder="Enter item name")
                ),
                block_kit.input_block(
                    "Description",
                    block_kit.plain_text_input("description", placeholder="Enter description", multiline=True),
                    optional=True
                ),
                block_kit.input_block(
                    "Category",
                    block_kit.select_menu(
                        "Select a category",
                        "category",
                        [
                            block_kit.option("Product", "product"),
                            block_kit.option("Service", "service"),
                            block_kit.option("Other", "other")
                        ]
                    )
                )
            ]
            
            return CommandResponse.form(
                "Create New Item",
                input_elements,
                submit_label="Create",
                ephemeral=True
            )
    
    # Register all the commands
    registry.register_command("profile", UserProfileCommand())
    registry.register_command("permissions", ListPermissionsCommand())
    registry.register_command("confirm", ConfirmActionCommand())
    registry.register_command("create-item", CreateItemCommand())
    
    # Test and demonstrate the commands
    print("Demonstrating various Block Kit responses:")
    
    # System status with custom blocks
    print("\n1. System Status (custom blocks):")
    response = registry.route_command("status", {})
    blocks = response.content
    
    # Print the blocks with indentation for readability
    import json
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    # User profile with information helper
    print("\n2. User Profile (information helper):")
    response = registry.route_command("profile", {})
    blocks = response.content
    
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    # Table formatting
    print("\n3. Permissions Table (table helper):")
    response = registry.route_command("permissions", {})
    blocks = response.content
    
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    # Confirmation with buttons
    print("\n4. Confirmation Dialog (confirmation helper):")
    response = registry.route_command("confirm", {})
    blocks = response.content
    
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    # Form with inputs
    print("\n5. Create Item Form (form helper):")
    response = registry.route_command("create-item", {})
    blocks = response.content
    
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    print("\nBlock Kit response formatting demonstration complete!")
    
    return registry


if __name__ == "__main__":
    print("PROGRESSIVE DEMO OF SLACK COMMANDS LIBRARY")
    print("This demonstrates the features implemented in Phases 1-6")
    
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
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 5 demo
    registry = phase5_demo(registry)
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 6 demo
    phase6_demo(registry) 