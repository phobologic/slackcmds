"""Tests for the command module."""

import unittest
from typing import Dict, List, Any, Optional

from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.validation import Parameter, ParameterType
from slackcmds.core import validation


class TestCommand(unittest.TestCase):
    """Tests for the Command class."""
    
    def test_command_init(self):
        """Test initializing a Command."""
        command = Command()
        command.name = "test"
        command.short_help = "Test command"
        command.accepts_arguments = True
        self.assertEqual(command.name, "test")
        self.assertEqual(command.short_help, "Test command")
        self.assertTrue(command.accepts_arguments)
        self.assertEqual(command.subcommands, {})
        self.assertEqual(command.parameters, [])
    
    def test_command_set_name(self):
        """Test setting a Command's name."""
        command = Command()
        command._set_name("test")
        self.assertEqual(command.name, "test")
    
    def test_command_set_help(self):
        """Test setting a Command's help text."""
        command = Command()
        command.set_help("Test command", "Detailed help", "test <arg>")
        self.assertEqual(command.short_help, "Test command")
        self.assertEqual(command.long_help, "Detailed help")
        self.assertEqual(command.usage_example, "test <arg>")
    
    def test_command_register_subcommand(self):
        """Test registering a subcommand."""
        command = Command()
        command._set_name("test")
        subcommand = Command()
        command.register_subcommand("subcommand", subcommand)
        self.assertEqual(command.subcommands["subcommand"], subcommand)
        self.assertEqual(subcommand.name, "test subcommand")
    
    def test_command_execute_implementation(self):
        """Test executing a Command with an implementation."""
        
        class CustomCommand(Command):
            def _execute_impl(self, context):
                return CommandResponse(f"Executed with {context['tokens']}")
        
        command = CustomCommand()
        command._set_name("test")
        command.short_help = "Test command"
        command.accepts_arguments = True
        
        context = {"tokens": ["arg1", "arg2"]}
        response = command.execute(context)
        self.assertEqual(response.content, "Executed with ['arg1', 'arg2']")
    
    def test_command_execute_no_implementation(self):
        """Test executing a Command without an implementation."""
        command = Command()
        command._set_name("test")
        command.short_help = "Test command"
        
        context = {}
        response = command.execute(context)
        self.assertIn("doesn't have an implementation", response.content)
    
    def test_command_validate(self):
        """Test validating a Command."""
        command = Command()
        command._set_name("test")
        command.short_help = "Test command"
        command.accepts_arguments = True
        
        # Add a parameter
        command.add_parameter(
            Parameter(
                name="name",
                type="string", 
                required=True,
                help_text="Your name"
            )
        )
        
        # Valid case
        context = {"tokens": ["John"]}
        response = command.validate(context)
        self.assertTrue(response.success)
        self.assertEqual(context["validated_params"]["name"], "John")
        
        # Invalid case - missing required parameter
        context = {"tokens": []}
        response = command.validate(context)
        self.assertFalse(response.success)
        self.assertIn("name: Required parameter missing", response.content)
    
    def test_command_show_help(self):
        """Test showing a Command's help message."""
        command = Command()
        command._set_name("test")
        command.short_help = "Test command"
        
        response = command.show_help()
        self.assertIn("test", response.content)
        self.assertIn("Base class for all command handlers", response.content)
    
    def test_command_help_detection(self):
        """Test detecting a help request."""
        command = Command()
        command._set_name("test")
        
        # With "help" as the first token
        context = {"tokens": ["help"]}
        response = command.execute(context)
        self.assertIn("Help: test", response.content)
        
        # Test with other tokens
        context = {"tokens": ["not-help"]}
        response = command.execute(context)
        self.assertIn("doesn't have an implementation", response.content)
    
    def test_has_custom_execution(self):
        """Test checking if a Command has custom execution."""
        # Command with implementation
        class CustomCommand(Command):
            def _execute_impl(self, context):
                return CommandResponse("Executed")
        
        command = CustomCommand()
        command._set_name("test")
        self.assertTrue(command._has_custom_execution())
        
        # Command without implementation
        command = Command()
        command._set_name("test")
        self.assertFalse(command._has_custom_execution())
    
    def test_show_invalid_subcommand_error(self):
        """Test showing an invalid subcommand error."""
        command = Command()
        command._set_name("test")
        command.register_subcommand("sub1", Command())
        command.register_subcommand("sub2", Command())
        
        response = command.show_invalid_subcommand_error("invalid")
        self.assertIn("not a valid subcommand", response.content)
        self.assertIn("Available Subcommands", response.content)
        self.assertIn("sub1", response.content)
        self.assertIn("sub2", response.content)
    
    def test_invalid_subcommand_detection(self):
        """Test detecting an invalid subcommand."""
        command = Command()
        command._set_name("test")
        subcommand = Command()
        command.register_subcommand("sub", subcommand)
        
        # Invalid subcommand
        context = {"tokens": ["invalid"]}
        response = command.execute(context)
        self.assertFalse(response.success)
        self.assertIn("not a valid subcommand", response.content)
        
        # Valid subcommand
        context = {"tokens": ["sub"]}
        response = command.execute(context)
        self.assertTrue(response.success)
    
    def test_command_with_registry_integration(self):
        """Test integrating a Command with a CommandRegistry."""
        from slackcmds.core.registry import CommandRegistry
        
        registry = CommandRegistry()
        
        # Define a command
        class WeatherCommand(Command):
            def _execute_impl(self, context):
                # Get the location from validated_params
                location = context.get("validated_params", {}).get("location", "unknown")
                return CommandResponse(f"Weather for {location}: Sunny")
        
        # Create command
        command = WeatherCommand()
        command._set_name("weather")
        command.short_help = "Get the weather"
        command.accepts_arguments = True
        
        # Add parameters
        command.add_parameter(
            Parameter(
                name="location",
                type="string",
                required=True,
                help_text="The location to get weather for"
            )
        )
        
        # Register with registry
        registry.register_command("weather", command)
        
        # Test execution - routing directly with tokens for simplicity
        context = {"tokens": ["Seattle"]}
        response = command.execute(context)
        self.assertEqual(response.content, "Weather for Seattle: Sunny")
        
        # We could also test through registry but we'd need to match its context format
        # response = registry.route_command("weather", {"text": "Seattle"})
        # self.assertEqual(response.content, "Weather for Seattle: Sunny")
        
        # Test help via execute method
        context = {"tokens": ["help"]}
        response = command.execute(context)
        self.assertIn("weather", response.content)
        
        # Test validation failure
        context = {"tokens": []}
        response = command.execute(context)
        self.assertIn("Required parameter missing", response.content)


if __name__ == "__main__":
    unittest.main()
