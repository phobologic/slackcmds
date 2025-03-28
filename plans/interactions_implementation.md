# SlackCmds Interaction Handling Implementation Plan

This document outlines a phased approach to implement interaction handling capabilities for SlackCmds library's interactive response types (form, confirmation, etc.).

## Overview

Currently, our library supports creating interactive Block Kit responses (forms, confirmations, tables, etc.), but lacks the infrastructure to handle the interactions when users engage with these elements. This plan details how to extend the library to:

1. Register interaction handlers
2. Route incoming interaction payloads
3. Provide context for stateful interactions
4. Update messages based on interaction results

## Phase 1: Core Interaction Infrastructure

### Goals
- Create base interaction handler classes
- Implement interaction payload routing
- Support basic button interactions

### Implementation Steps

1. [ ] Create a new module `slackcmds/core/interactions.py`:
   - [ ] Define an `InteractionHandler` base class
   - [ ] Create an `InteractionRegistry` for registering handlers
   - [ ] Implement utility functions for parsing interaction payloads

2. [ ] Extend `server.py` to handle interaction payloads:
   - [ ] Add a Bolt listener for `action` and `view_submission` events
   - [ ] Route payloads to appropriate handlers

3. [ ] Update `CommandResponse` class to support interaction handlers:
   - [ ] Add methods to attach interaction metadata
   - [ ] Generate unique identifiers for interactive elements

4. [ ] Create basic button interaction handling:
   - [ ] Implement a `ButtonHandler` class
   - [ ] Add helper methods to `CommandResponse` for button responses

### Demo Code

```python
# Example of registering a button handler
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.interactions import ButtonHandler

class ApprovalCommand(Command):
    """Command that requires approval."""
    
    def execute(self, context):
        # Create confirmation with buttons
        response = CommandResponse.confirmation(
            title="Approval Required",
            message="Do you want to proceed with this action?",
            choices=[
                {"text": "Approve", "value": "approve", "style": "primary"},
                {"text": "Reject", "value": "reject", "style": "danger"}
            ]
        )
        
        # Register button handlers
        response.register_button_handler("approve", self.handle_approve)
        response.register_button_handler("reject", self.handle_reject)
        
        return response
    
    def handle_approve(self, payload, context):
        # Handle approval action
        return CommandResponse.success("Action approved!")
    
    def handle_reject(self, payload, context):
        # Handle rejection action
        return CommandResponse.error("Action rejected.")
```

## Phase 2: Form Submission Handling

### Goals
- Support modal form submissions
- Implement validation for form inputs
- Allow updating forms based on partial inputs

### Implementation Steps

1. [ ] Create form handling components:
   - [ ] Implement a `FormHandler` class
   - [ ] Add form state management utilities
   - [ ] Create validation framework for form inputs

2. [ ] Extend server integration:
   - [ ] Add support for `view_submission` payloads
   - [ ] Implement form state persistence

3. [ ] Update `CommandResponse` class:
   - [ ] Enhance `form()` method to support handlers
   - [ ] Add validation error formatting

4. [ ] Create helpers for common form patterns:
   - [ ] Input validation utilities
   - [ ] Form state management
   - [ ] Response transformation

### Demo Code

```python
# Example of a form with validation and submission handling
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.interactions import FormHandler

class UserRegistrationCommand(Command):
    """Register a new user."""
    
    def execute(self, context):
        # Create form with input fields
        response = CommandResponse.form(
            title="User Registration",
            input_elements=[
                {
                    "label": "Username",
                    "name": "username",
                    "type": "text_input",
                    "placeholder": "Enter username"
                },
                {
                    "label": "Email",
                    "name": "email",
                    "type": "text_input",
                    "placeholder": "Enter email"
                }
            ]
        )
        
        # Register form submission handler
        response.register_form_handler(self.handle_registration)
        
        return response
    
    def handle_registration(self, payload, context):
        # Extract form values
        values = payload.get("view", {}).get("state", {}).get("values", {})
        
        # Validate input
        username = values.get("username", {}).get("value", "")
        email = values.get("email", {}).get("value", "")
        
        if not username:
            return FormHandler.validation_error("username", "Username is required")
        
        if not email or "@" not in email:
            return FormHandler.validation_error("email", "Valid email is required")
        
        # Process valid submission
        # ... registration logic ...
        
        return CommandResponse.success(f"User {username} registered successfully!")
```

## Phase 3: Interaction Context and State Management

### Goals
- Implement context passing for interactions
- Create state management for multi-step interactions
- Support conversation-like flows

### Implementation Steps

1. [ ] Create interaction context management:
   - [ ] Implement `InteractionContext` class
   - [ ] Add state persistence mechanisms
   - [ ] Create utilities for context serialization

2. [ ] Extend existing handlers:
   - [ ] Update `ButtonHandler` and `FormHandler` to use context
   - [ ] Add middleware for context injection

3. [ ] Implement conversation-like flows:
   - [ ] Create a `Conversation` class for multi-step interactions
   - [ ] Add state transition management
   - [ ] Implement conversation history

4. [ ] Add timeout and expiration for interactions:
   - [ ] Implement TTL for interaction handlers
   - [ ] Add cleanup mechanisms for expired handlers

### Demo Code

```python
# Example of a multi-step interaction with state
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.interactions import Conversation

class OrderProcessCommand(Command):
    """Process a new order."""
    
    def execute(self, context):
        # Start a conversation
        conversation = Conversation("order_process")
        
        # Define the first step
        response = CommandResponse.form(
            title="New Order",
            input_elements=[
                {
                    "label": "Product",
                    "name": "product",
                    "type": "select",
                    "options": [
                        {"text": "Product A", "value": "a"},
                        {"text": "Product B", "value": "b"}
                    ]
                }
            ]
        )
        
        # Register as first step in conversation
        conversation.add_step("product_selection", response, self.handle_product_selection)
        
        # Start the conversation
        return conversation.start()
    
    def handle_product_selection(self, payload, context):
        # Get selected product
        values = payload.get("view", {}).get("state", {}).get("values", {})
        product = values.get("product", {}).get("selected_option", {}).get("value")
        
        # Store in conversation state
        context.conversation.set_state("product", product)
        
        # Create next form for quantity
        response = CommandResponse.form(
            title=f"Order Quantity for {product.upper()}",
            input_elements=[
                {
                    "label": "Quantity",
                    "name": "quantity",
                    "type": "number_input"
                }
            ]
        )
        
        # Continue to next step
        return context.conversation.next_step("quantity_selection", response, self.handle_quantity)
    
    def handle_quantity(self, payload, context):
        # Get quantity
        values = payload.get("view", {}).get("state", {}).get("values", {})
        quantity = values.get("quantity", {}).get("value")
        
        # Get product from state
        product = context.conversation.get_state("product")
        
        # Process order
        # ... order processing logic ...
        
        # End conversation with success
        return CommandResponse.success(
            f"Order created: {quantity}x Product {product.upper()}",
            ephemeral=False
        )
```

## Phase 4: Advanced Interaction Patterns

### Goals
- Support dynamic updates to messages
- Implement pagination for large data sets
- Add support for complex interaction patterns

### Implementation Steps

1. [ ] Implement message update utilities:
   - [ ] Add methods to update existing messages
   - [ ] Create progressive disclosure patterns
   - [ ] Support replacing vs. appending content

2. [ ] Create pagination system:
   - [ ] Implement data pagination for large result sets
   - [ ] Add navigation controls
   - [ ] Support both numeric and cursor-based pagination

3. [ ] Add support for complex interactions:
   - [ ] Implement cascading selects
   - [ ] Create dependent form fields
   - [ ] Support conditional form elements

4. [ ] Implement error handling and recovery:
   - [ ] Add retry mechanisms
   - [ ] Implement interaction timeout recovery
   - [ ] Create fallback patterns

### Demo Code

```python
# Example of paginated results with dynamic updates
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse
from slackcmds.core.interactions import Paginator

class SearchResultsCommand(Command):
    """Search and display paginated results."""
    
    def execute(self, context):
        query = context.params.get("query", "")
        
        # Simulate search results
        results = self._perform_search(query)
        
        # Create paginator
        paginator = Paginator(
            data=results,
            page_size=5,
            formatter=self._format_result_item
        )
        
        # Initial response with first page
        response = paginator.get_page_response(
            title=f"Search Results for '{query}'",
            current_page=1
        )
        
        # Register navigation handlers
        paginator.register_handlers(response)
        
        return response
    
    def _perform_search(self, query):
        # Simulate search logic
        return [{"title": f"Result {i} for {query}", "score": i * 10} 
                for i in range(1, 25)]
    
    def _format_result_item(self, item):
        # Format a single result item
        return f"*{item['title']}* (Score: {item['score']})"
```

## Phase 5: Integration and Documentation

### Goals
- Ensure seamless integration with existing components
- Create comprehensive documentation
- Provide examples and templates

### Implementation Steps

1. [ ] Finalize integration with existing components:
   - [ ] Update `Command` and `CommandRegistry` classes
   - [ ] Ensure backward compatibility
   - [ ] Add migration utilities

2. [ ] Create comprehensive documentation:
   - [ ] Write API documentation
   - [ ] Create tutorials for common patterns
   - [ ] Add commented examples

3. [ ] Build example templates:
   - [ ] Create template library for common interaction patterns
   - [ ] Add sample implementations
   - [ ] Build starter templates

4. [ ] Implement testing framework:
   - [ ] Create interaction testing utilities
   - [ ] Add mocking support for Slack interactions
   - [ ] Implement integration tests

### Demo Code

```python
# Example documentation and usage patterns
"""
# SlackCmds Interaction Handling

This module provides tools for handling user interactions with Slack messages
and modals created by your commands.

## Basic Usage

```python
from slackcmds.core.command import Command
from slackcmds.core.response import CommandResponse

class MyInteractiveCommand(Command):
    def execute(self, context):
        # Create an interactive response
        response = CommandResponse.confirmation(
            title="Confirmation Needed",
            message="Are you sure you want to proceed?",
            choices=[
                {"text": "Yes", "value": "yes", "style": "primary"},
                {"text": "No", "value": "no", "style": "danger"}
            ]
        )
        
        # Register handlers for the interactions
        response.register_button_handler("yes", self.handle_yes)
        response.register_button_handler("no", self.handle_no)
        
        return response
        
    def handle_yes(self, payload, context):
        # Handle "Yes" button click
        return CommandResponse.success("Action confirmed!")
        
    def handle_no(self, payload, context):
        # Handle "No" button click
        return CommandResponse.error("Action cancelled.")
```

## Advanced Patterns

For more complex interactions, use the Conversation class:

```python
from slackcmds.core.interactions import Conversation

# Start a multi-step interaction
conversation = Conversation("workflow_name")

# Add steps with their handlers
conversation.add_step("step1", response1, handler1)
conversation.add_step("step2", response2, handler2)

# Start the conversation with the first step
return conversation.start()
```

See more examples in the documentation.
"""
```

## Summary

This phased approach allows for incremental implementation while providing value at each stage:

1. **Phase 1** establishes the core infrastructure for handling button interactions
2. **Phase 2** adds support for form submissions and validation
3. **Phase 3** implements context and state management for multi-step interactions
4. **Phase 4** enhances the library with advanced interaction patterns
5. **Phase 5** ensures smooth integration and provides comprehensive documentation

Each phase builds upon the previous one, allowing for testing and feedback throughout the implementation process. 