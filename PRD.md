# Product Requirements Document: Slack Command Library

## Overview
A Python library that provides a clean, intuitive framework for building Slack slash commands with nested subcommand support. The library will handle command registration, routing, help text generation, and error handling. This library aims to fill a gap in the existing Slack development ecosystem by providing structured support for complex command hierarchies that would otherwise require custom implementation.

## Core Features

### 1. Command Structure
- Support for top-level commands and nested subcommands with unlimited nesting depth
- Pythonic approach using class-based commands
- Command names set during registration 
- Separation of business logic from command structure

### 2. Command Registration
- Registry for top-level commands
- Explicit registration of subcommands
- Support for docstrings as command documentation
- Optional ability to override both short and long help text

### 3. Command Execution
- Routing of commands to appropriate handlers
- Context passing to commands via context object
- Input validation at the command level
- Stateless execution (state management handled by consuming applications)

### 4. Command Response
- Standard CommandResponse class with support for:
  - Text responses
  - Block Kit formatted responses
  - Ephemeral vs. channel visibility
  - Success/error status
- Helper methods for common response patterns

### 5. Help System
- Automatic generation of help text from docstrings
- Brief descriptions for command listings
- Detailed help for specific commands
- Support for "help" as a subcommand at any level
- Developer ability to override generated help text

### 6. Integration with Slack Bolt
- Built on the Slack Bolt framework
- Focus on slash commands only
- Parameter collection via Slack pop-ups rather than inline parameters
- Environment variable configuration
- Proper text-based logging of requests and errors

## Technical Requirements

### 1. Code Structure
```
slackcmds/
├── __init__.py
├── commands/
│   ├── __init__.py
│   ├── user_commands.py
│   └── tests/
│       ├── __init__.py
│       └── test_user_commands.py
├── core/
│   ├── __init__.py
│   ├── command.py
│   ├── registry.py
│   └── tests/
│       ├── __init__.py
│       ├── test_command.py
│       └── test_registry.py
├── server.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_server.py
├── .env.example
├── README.md
├── requirements.txt
└── setup.py
```

### 2. Dependencies
- slack_bolt: For Slack integration
- pytest: For testing

### 3. Configuration
- Environment variables for all configuration
- Configurable logging level and output
- Command name configuration

### 4. Documentation
- Google-style docstrings
- Comprehensive README
- Example implementations

### 5. Testing
- Unit tests located in tests/ subdirectories
- High test coverage
- Integration tests for end-to-end functionality

## Sample Implementation

### Core Command Class
```python
class Command:
    """Base class for all command handlers.
    
    This class serves as the foundation for all commands in the system.
    It provides common functionality like help text generation and 
    subcommand registration.
    """
    
    def __init__(self):
        """Initialize a new Command instance."""
        self.name = None
        self.subcommands = {}
        self.short_help = None
        self.long_help = None
    
    def _set_name(self, name):
        """Set the command name (called during registration)."""
        self.name = name
        return self
    
    def set_help(self, short_help=None, long_help=None):
        """Override the default help text generated from docstrings."""
        self.short_help = short_help
        self.long_help = long_help
        return self
        
    def execute(self, context=None):
        """Execute the command logic."""
        try:
            logger.debug(f"Executing command: {self.name}")
            
            # Validate input if needed
            validation_result = self.validate(context)
            if not validation_result.success:
                return validation_result
            
            if self.subcommands:
                return self.show_help()
            
            return CommandResponse(
                f"Command '{self.name}' doesn't have an implementation.",
                success=False
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in {self.name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            return CommandResponse(
                f"An unexpected error occurred: {str(e)}",
                success=False
            )
    
    def validate(self, context=None):
        """Validate command input before execution.
        
        Override this method to implement custom validation logic.
        
        Returns:
            CommandResponse: A response object indicating validation success/failure.
        """
        return CommandResponse("Input valid", success=True)
    
    def show_help(self, specific_subcommand=None):
        """Show detailed help for this command or a specific subcommand."""
        # Help generation logic using docstrings or overridden help text
    
    def register_subcommand(self, name, command_instance):
        """Register a subcommand."""
        command_instance._set_name(name)
        self.subcommands[name] = command_instance
        return command_instance
```

### Command Response Class
```python
class CommandResponse:
    """Response object for command execution results."""
    
    def __init__(self, content, success=True, ephemeral=True):
        """Initialize a new command response.
        
        Args:
            content: Text or Block Kit content for the response
            success: Whether the command was successful
            ephemeral: Whether the response should be visible only to the user
        """
        self.content = content
        self.success = success
        self.ephemeral = ephemeral
    
    def as_dict(self):
        """Convert to format expected by Slack API."""
        if isinstance(self.content, str):
            return {
                "text": self.content,
                "response_type": "ephemeral" if self.ephemeral else "in_channel"
            }
        else:
            # Block Kit format
            return {
                "blocks": self.content,
                "response_type": "ephemeral" if self.ephemeral else "in_channel"
            }
    
    @classmethod
    def error(cls, message):
        """Create a standardized error response."""
        return cls(f":x: Error: {message}", success=False)
    
    @classmethod
    def success(cls, message, ephemeral=True):
        """Create a standardized success response."""
        return cls(f":white_check_mark: {message}", success=True, ephemeral=ephemeral)
    
    @classmethod
    def with_blocks(cls, blocks, success=True, ephemeral=True):
        """Create a response with Block Kit blocks."""
        return cls(blocks, success=success, ephemeral=ephemeral)
```

### Registry Implementation
```python
class CommandRegistry:
    """Registry for top-level commands."""
    
    def __init__(self):
        """Initialize a new command registry."""
        self.top_level_commands = {}
        self.logger = logging.getLogger('slack_commands.registry')
    
    def register_command(self, name, command_instance):
        """Register a top-level command."""
        command_instance._set_name(name)
        self.top_level_commands[name] = command_instance
        self.logger.info(f"Registered top-level command: {name}")
        return command_instance
    
    def route_command(self, command_string, context=None):
        """Route a command string to the appropriate handler."""
        # Command routing logic...
```

### Server Integration
```python
# Initialize the Slack Bolt app with environment variables
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Handle the slash command
@app.command("/sologm")
def handle_sologm_command(ack, command, say):
    # Command handling logic...
```

## Technical Constraints

- Python Version: 3.13+
- Follows semantic versioning for releases
- Stateless command execution
- Parameters collected via Slack pop-ups using Bolt's built-in capabilities

## Out of Scope (Future Considerations)

The following features are intentionally excluded from the initial implementation but may be considered for future releases:

- Middleware or hooks for command execution
- Authorization/permission system
- Testing utilities and helpers
- Support for additional Slack interaction models beyond slash commands
- Advanced state management
- Retry mechanisms for failed commands

## Next Steps
1. Implement the core command and registry classes
2. Create the CommandResponse class
3. Develop the basic server integration with Slack Bolt
4. Implement input validation framework
5. Create sample commands for demonstration
6. Write comprehensive tests
7. Create documentation and usage examples
