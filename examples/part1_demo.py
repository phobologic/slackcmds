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