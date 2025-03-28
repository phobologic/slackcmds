"""
Slack Commands Library

A Python library that provides a clean, intuitive framework for building
Slack slash commands with nested subcommand support.
"""

import logging

from .core import Command, CommandResponse, CommandRegistry

__version__ = '0.1.0'
__all__ = ['Command', 'CommandResponse', 'CommandRegistry']

# Set up package-level logger
logging.getLogger('slackcmds').addHandler(logging.NullHandler())
