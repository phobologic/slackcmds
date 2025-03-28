#!/usr/bin/env python3
"""
Progressive demo of the Slack Commands Library.

This script progressively demonstrates the features implemented in:
- Phase 1: Core Command and Response Structure
- Phase 2: Command Registry and Routing
- Phase 3: Help System Implementation
"""

import time
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
            self.set_help(use_block_kit=True)
    
    config_cmd = registry.register_command("config", ConfigCommand())
    
    class GetConfigCommand(Command):
        """Get the value of a configuration setting."""
        
        def __init__(self):
            super().__init__()
            self.set_help(
                usage_example="config get <setting_name>",
                use_block_kit=True
            )
        
        def execute(self, context=None):
            return CommandResponse("Configuration setting value would be displayed here")
    
    config_cmd.register_subcommand("get", GetConfigCommand())
    
    class SetConfigCommand(Command):
        """Set a configuration setting value."""
        
        def __init__(self):
            super().__init__()
            self.set_help(
                usage_example="config set <setting_name> <value>",
                use_block_kit=True
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


if __name__ == "__main__":
    print("PROGRESSIVE DEMO OF SLACK COMMANDS LIBRARY")
    print("This demonstrates the features implemented in Phases 1, 2, and 3")
    
    # Run Phase 1 demo
    HelloCommand = phase1_demo()
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 2 demo
    registry, user_cmd, list_cmd = phase2_demo(HelloCommand)
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 3 demo
    phase3_demo(registry, user_cmd, list_cmd) 