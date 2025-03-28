#!/usr/bin/env python3
"""
Progressive demo of the Slack Commands Library.

This script progressively demonstrates the features implemented in:
- Phase 1: Core Command and Response Structure
- Phase 2: Command Registry and Routing
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


if __name__ == "__main__":
    print("PROGRESSIVE DEMO OF SLACK COMMANDS LIBRARY")
    print("This demonstrates the features implemented in Phase 1 and 2")
    
    # Run Phase 1 demo
    HelloCommand = phase1_demo()
    
    # Pause for readability
    time.sleep(1)
    
    # Run Phase 2 demo
    phase2_demo(HelloCommand) 