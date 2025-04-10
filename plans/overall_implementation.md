# Slack Command Library Implementation Plan

This plan outlines the step-by-step process for building the Slack Command Library according to the PRD. Each phase builds on the previous one, with demonstrations to validate functionality before moving forward.

## Phase 1: Core Command and Response Structure

- [x] **Set up development environment**
  - Create a virtual environment using `uv venv`
  - Activate virtual env

- [x] **Create base project structure**
  - Set up package directory structure
  - Set up logging configuration
  - Create `.env.example` file with required variables

- [x] **Manage dependencies with uv**
  - Initialize dependencies with `uv add install slack_bolt`
  - Add dev dependencies `uv add --dev pytest`
  - Document dependency management process in README

- [x] **Implement Command class**
  - Basic initialization with name and subcommands
  - Implement help text management
  - Create basic execution method
  - Set up the command validation framework

- [x] **Implement CommandResponse class**
  - Create response initialization
  - Add support for text and Block Kit responses
  - Implement helper methods for common response types
  - Add conversion to Slack API format

**Demo 1:** Create a simple command class that can be instantiated and returns a basic response. Demonstrate direct execution without Slack integration.

```python
# Demo script
# First, ensure you're in the uv virtual environment

# Run the following script
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse

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
```

## Phase 2: Command Registry and Routing

- [x] **Implement CommandRegistry class**
  - Create registration methods for top-level commands
  - Implement command routing logic
  - Add support for extracting subcommands from input

- [x] **Implement subcommand registration**
  - Add methods for registering subcommands
  - Create logic for linking parent and child commands
  - Implement command chain parsing

- [x] **Command execution flow**
  - Implement command string tokenization
  - Create context object structure
  - Set up execution pipeline

**Demo 2:** Register commands and subcommands, then route command strings to their handlers.

```python
# Demo script
registry = CommandRegistry()

# Register top-level command
hello_cmd = registry.register_command("hello", HelloCommand())

# Register subcommand
class WorldCommand(Command):
    """Show a greeting to the world."""
    
    def execute(self, context=None):
        return CommandResponse.success("Hello, world!", ephemeral=False)

hello_cmd.register_subcommand("world", WorldCommand())

# Test routing
response = registry.route_command("hello", {})
print("Route 'hello':", response.as_dict())

response = registry.route_command("hello world", {})
print("Route 'hello world':", response.as_dict())

response = registry.route_command("unknown", {})
print("Route 'unknown':", response.as_dict())
```

## Phase 3: Help System Implementation

- [x] **Automatic help text generation**
  - Extract docstrings from command classes
  - Format help text for different display contexts
  - Create logic for command listings

- [x] **Implement help command functionality**
  - Add help as a virtual subcommand for all commands
  - Create help text formatting for different levels
  - Support for overriding generated help texts

- [x] **Format help responses**
  - Create text-based help display
  - Implement Block Kit formatted help display
  - Add command usage examples

**Demo 3:** Show automatically generated help, override help, and access help as a subcommand.

```python
# Demo script
registry = CommandRegistry()

class UserCommand(Command):
    """Manage users in the system.
    
    This command provides functionality for listing, adding,
    and removing users from the system.
    """
    
    def execute(self, context=None):
        return self.show_help()

user_cmd = registry.register_command("user", UserCommand())

class ListCommand(Command):
    """List all users in the system."""
    
    def execute(self, context=None):
        return CommandResponse.success("User list would be shown here")

user_cmd.register_subcommand("list", ListCommand())

# Test help
response = registry.route_command("help", {})
print("Top-level help:", response.as_dict())

response = registry.route_command("user help", {})
print("User command help:", response.as_dict())

# Test overridden help
list_cmd = user_cmd.subcommands["list"]
list_cmd.set_help("List users", "Display all users in a formatted table")
response = registry.route_command("user list help", {})
print("List command help (overridden):", response.as_dict())
```

## Phase 4: Server Integration with Slack Bolt

- [x] **Set up Slack Bolt integration**
  - Create server initialization
  - Implement command handling
  - Set up environment variable configuration

- [x] **Command context creation**
  - Extract command information from Slack requests
  - Create context objects from Slack events
  - Handle command acknowledge and response

- [x] **Request and error logging**
  - Implement logging for incoming requests
  - Add error capture and logging
  - Create debug information for troubleshooting

**Demo 4:** Set up a minimal Slack app that responds to slash commands using the library.

```python
# server.py demo
from slack_bolt import App
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Slack Bolt app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Set up command registry
registry = CommandRegistry()

# Register commands (reuse previous commands)
user_cmd = registry.register_command("user", UserCommand())
user_cmd.register_subcommand("list", ListCommand())

# Handle the slash command
@app.command("/demo")
def handle_demo_command(ack, command, say):
    # Acknowledge the command request
    ack()
    
    # Extract the command text
    command_text = command["text"]
    
    # Create context from command
    context = {
        "user_id": command["user_id"],
        "channel_id": command["channel_id"],
        "team_id": command["team_id"],
        "text": command_text,
        # Add other relevant information
    }
    
    # Route the command
    response = registry.route_command(command_text, context)
    
    # Send the response
    say(**response.as_dict())

# Start the app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
```

## Phase 5: Input Validation Framework

- [x] **Implement validation framework**
  - Create standard validation methods
  - Implement validation error handling
  - Support for required parameters checking

- [x] **Parameter extraction**
  - Parse command arguments
  - Support for different parameter types
  - Parameter requirement checking

- [x] **Context validation**
  - Validate request context
  - Command-specific validation logic
  - Error response standardization

**Demo 5:** Demonstrate commands with validation that require specific parameters.

```python
# Demo script with validation
class AddUserCommand(Command):
    """Add a new user to the system.
    
    Usage: user add <username> <email>
    """
    
    def validate(self, context=None):
        # Get tokens from context
        tokens = context.get("tokens", [])
        
        # Check for required parameters
        if len(tokens) < 2:
            return CommandResponse.error(
                "Missing required parameters. Usage: user add <username> <email>"
            )
        
        # Validate email format
        email = tokens[1]
        if not "@" in email:
            return CommandResponse.error("Invalid email format")
            
        return CommandResponse("Validation passed", success=True)
    
    def execute(self, context=None):
        # Get parameters from context
        tokens = context.get("tokens", [])
        username = tokens[0]
        email = tokens[1]
        
        # Would normally save user here
        
        return CommandResponse.success(
            f"Added user {username} with email {email}",
            ephemeral=False
        )

# Register the command
user_cmd.register_subcommand("add", AddUserCommand())

# Test the command with valid input
context = {"tokens": ["john", "john@example.com"]}
response = registry.route_command("user add", context)
print("Valid input:", response.as_dict())

# Test with invalid input
context = {"tokens": ["jane"]}
response = registry.route_command("user add", context)
print("Missing parameter:", response.as_dict())

context = {"tokens": ["jane", "invalid-email"]}
response = registry.route_command("user add", context)
print("Invalid email:", response.as_dict())
```

## Phase 6: Block Kit Response Formatting

- [x] **Implement Block Kit helper methods**
  - Create methods for common Block Kit components
  - Add response formatting utilities
  - Support for rich formatting

- [x] **Response templates**
  - Standard layouts for different response types
  - Helper methods for consistent UX
  - Formatting for different contexts

- [x] **Support for ephemeral vs. channel responses**
  - Distinguish between private and public responses
  - Clear API for controlling visibility
  - Default visibility settings

**Demo 6:** Show commands that return rich Block Kit formatted responses.

```python
# Demo with Block Kit responses
class StatusCommand(Command):
    """Show system status with rich formatting."""
    
    def execute(self, context=None):
        # Create Block Kit blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "System Status"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Database:*\n:white_check_mark: Online"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*API:*\n:white_check_mark: Operational"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Last updated: just now"
                    }
                ]
            }
        ]
        
        return CommandResponse.with_blocks(blocks, ephemeral=False)

# Register the command
registry.register_command("status", StatusCommand())

# Test the command
response = registry.route_command("status", {})
print("Block Kit response:", response.as_dict())
```

## Phase 7: Testing and Documentation

- [x] **Unit testing**
  - Create test fixtures
  - Implement command and registry tests
  - Response formatting tests

- [x] **Integration testing**
  - Mock Slack API interactions
  - End-to-end test cases
  - Mock command execution flow

- [x] **Documentation**
  - Update README with usage examples
  - Add docstrings to all public methods

**Demo 7:** No demo needed, skip.

## Conclusion

This implementation plan provides a structured approach to building the Slack Command Library. By following these phases sequentially, you'll create a robust library that meets all the requirements in the PRD while allowing for testing and validation at each step.

Each phase builds on the previous ones, adding functionality incrementally and providing opportunities to verify that everything is working as expected before moving on. The demos at the end of each phase serve as both validation and documentation of how to use the features implemented in that phase.
