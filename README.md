# Slack Commands Library

A Python library that provides a clean, intuitive framework for building Slack slash commands with nested subcommand support. This library helps you organize complex command hierarchies and provides automatic help text generation, input validation, and rich response formatting.

## Features

- Support for top-level commands and nested subcommands with unlimited nesting depth
- Pythonic approach using class-based commands
- Automatic help text generation from docstrings
- Clean command routing and execution
- Robust input validation framework
- Rich response formatting with Block Kit
- Integration with Slack Bolt framework
- Comprehensive testing support

## Installation

### Prerequisites

- Python 3.8+
- A Slack workspace with permissions to add apps

### Using UV (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install slackcmds
uv pip install slackcmds
```

### Using pip

```bash
pip install slackcmds
```

### From source

```bash
git clone https://github.com/phobologic/slackcmds.git
cd slackcmds

# Using UV (Recommended)
uv venv
source .venv/bin/activate
uv sync
uv pip install -e .
```

## Quick Start

### Basic Usage

```python
from slack_bolt import App
from slackcmds.core.command import Command
from slackcmds.core.registry import CommandRegistry
from slackcmds.core.response import CommandResponse

# Initialize the app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Create command registry
registry = CommandRegistry()

# Define a command
class HelloCommand(Command):
    """Say hello to the user."""
    
    def _execute_impl(self, context):
        user_id = context.get("user_id", "user")
        return CommandResponse.success(f"Hello, <@{user_id}>!")

# Register command
registry.register_command("hello", HelloCommand())

# Handle slash command
@app.command("/demo")
def handle_command(ack, command, say):
    ack()
    context = {
        "user_id": command["user_id"], 
        "text": command["text"],
        "channel_id": command["channel_id"],
        "team_id": command["team_id"]
    }
    response = registry.route_command(command["text"], context)
    say(**response.as_dict())

# Start the app
if __name__ == "__main__":
    app.start(port=3000)
```

### Command with Subcommands

```python
class WeatherCommand(Command):
    """Get weather information."""
    
    def __init__(self):
        super().__init__()
        self.register_subcommand("today", TodayWeatherCommand())
        self.register_subcommand("forecast", ForecastWeatherCommand())
    
    def _execute_impl(self, context):
        # Default to showing help when called without subcommand
        return self.show_help()

class TodayWeatherCommand(Command):
    """Get today's weather."""
    
    def _execute_impl(self, context):
        return CommandResponse.success("Today's weather: Sunny and 75°F")

class ForecastWeatherCommand(Command):
    """Get the weather forecast."""
    
    def _execute_impl(self, context):
        forecast = [
            "Today: Sunny and 75°F",
            "Tomorrow: Partly cloudy and 72°F",
            "Wednesday: Rainy and 65°F"
        ]
        return CommandResponse("\n".join(forecast), ephemeral=False)

# Register with registry
registry.register_command("weather", WeatherCommand())
```

### Command with Parameter Validation

```python
from slackcmds.core.validation import Parameter, min_length, max_value

class AddUserCommand(Command):
    """Add a new user to the system."""
    
    def __init__(self):
        super().__init__()
        self.add_parameters([
            Parameter("username", "string", required=True, 
                      validators=[min_length(3)],
                      help_text="Username (min 3 characters)"),
            Parameter("email", "email", required=True,
                      help_text="Valid email address"),
            Parameter("role", "choice", required=False,
                      choices=["admin", "user", "guest"], default="user",
                      help_text="User role (default: user)")
        ])
    
    def _execute_impl(self, context):
        params = context["validated_params"]
        username = params["username"]
        email = params["email"]
        role = params["role"]
        
        return CommandResponse.success(
            f"Added user {username} with email {email} and role {role}"
        )
```

### Rich Response Formatting

```python
from slackcmds.core import block_kit

class StatusCommand(Command):
    """Show system status with rich formatting."""
    
    def _execute_impl(self, context):
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
```

## API Reference

### Core Classes

- `Command`: Base class for all command handlers
- `CommandRegistry`: Manages top-level commands and routing
- `CommandResponse`: Response object for command execution results
- `Parameter`: Defines a parameter for command validation

### Command Class Methods

- `_execute_impl(self, context)`: Override to implement command logic
- `validate(self, context)`: Validate command input
- `show_help(self, specific_subcommand=None)`: Show help for command
- `register_subcommand(self, name, command_instance)`: Register a subcommand
- `add_parameter(self, parameter)`: Add a parameter definition
- `add_parameters(self, parameters)`: Add multiple parameter definitions

### Command Response Factory Methods

- `CommandResponse.success(message, ephemeral=True)`: Create success response
- `CommandResponse.error(message)`: Create error response
- `CommandResponse.with_blocks(blocks, success=True, ephemeral=True)`: Create Block Kit response
- `CommandResponse.information(title, details, ephemeral=True)`: Create information message
- `CommandResponse.confirmation(title, message, choices, ephemeral=True)`: Create confirmation dialog
- `CommandResponse.table(title, headers, rows, ephemeral=True)`: Create table response
- `CommandResponse.form(title, input_elements, submit_label="Submit", ephemeral=True)`: Create form

## Testing

The library includes comprehensive testing utilities. See the `tests/` directory for examples.

### Running Tests

```bash
# Using UV (Recommended)
uv sync
uv run pytest

# or run with debug output
uv run pytest -o log_cli_level=DEBUG -v
```

## Development

### Setting up a development environment

```bash
# Clone the repository
git clone https://github.com/phobologic/slackcmds.git
cd slackcmds

# Create and activate a virtual environment with UV
uv venv
source .venv/bin/activate

# Install required packages
uv sync

# Install the package with development dependencies
uv pip install -e .
```

## Examples

Check the `examples/` directory for more detailed examples.

### Slack Integration Example

The repository includes a comprehensive example (`examples/server_demo.py`) that demonstrates how to integrate the library with Slack:

- Complete Slack Bolt app setup with Socket Mode support
- Multiple command examples with nested subcommands
- Input validation demonstration
- Rich Block Kit formatting examples
- Detailed step-by-step setup instructions in the file header

This example includes instructions in its docstring on how to:
1. Create a Slack app in the Slack API Console
2. Set up Socket Mode
3. Configure slash commands
4. Set up Bot Token Scopes
5. Install the app to your workspace
6. Run the demo with proper environment variables (with uv: `uv run python ./examples/server_demo.py` after you setup the necessary env vars)

## License

MIT
