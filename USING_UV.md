# UV for Python Library Development

UV is an extremely fast Python package and project manager written in Rust that can replace pip, virtualenv, pip-tools, and more. This guide covers the basics for Python library development.

## Installation

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# With pip (as fallback)
pip install uv
```

## Key Features for Library Development

- **10-100x faster** than traditional Python tooling
- **Single binary** that replaces multiple tools
- **Drop-in replacement** for familiar pip/virtualenv workflows
- **Modern dependency management** with lockfiles

## Basic Commands (Traditional → UV)

### Virtual Environments

```bash
# Create environment (replacing virtualenv)
uv venv                       # Creates .venv in current directory 

# Activate the environment
source .venv/bin/activate     # Same as virtualenv/venv
```

### Package Management

```bash
# Install dependencies (modern UV approach)
uv add requests               # Add a package to your project
uv add --group dev pytest     # Add to a specific dependency group

# Legacy-compatible approach (replacing pip)
uv pip install requests       # Install a single package
uv pip install -r requirements.txt    # Install from requirements

# Pin dependencies
uv lock                       # Create uv.lock file (modern approach)
uv pip compile requirements.in -o requirements.txt  # Create lockfile (legacy-compatible)
uv sync                       # Sync environment with lockfile (modern)
uv pip sync requirements.txt  # Sync environment with lockfile (legacy-compatible)
```

### Project-specific Workflows

```bash
# For library development, define dependencies in pyproject.toml
[project]
name = "my-library"
version = "0.1.0"
dependencies = ["requests>=2.28.0", "pydantic"]

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
```

Then work with them:

```bash
# Install your project in development mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Building and Publishing

```bash
# Build package distributions
uv build

# Publish to PyPI
uv publish
```

## Advanced Features

### Dependency Groups

```bash
# Add dependencies to specific groups
uv add --group dev pytest black
uv add requests pydantic

# Install only specific groups
uv pip sync --only-group dev
```

### Command-line Tool Management

```bash
# Run a tool without installing (like pipx run)
uvx black .                   # Run black formatter

# Install a tool globally (like pipx install)
uv tool install ruff          # Install ruff linter
```

### Python Version Management

```bash
# Install and use specific Python versions
uv python install 3.10 3.11 3.12
uv venv --python 3.11          # Create venv with specific Python
```

## Migration Tips

1. **Incremental adoption**: UV is a drop-in replacement, so you can adopt it gradually
2. **Keep your workflows**: Continue using requirements.txt or pyproject.toml
3. **Performance boost**: Experience immediate speed improvements without configuration
4. **Lock dependencies**: Use `uv pip compile` instead of pip-tools

## Common Project Tasks

```bash
# Start a new library project
mkdir my-library && cd my-library
uv venv
source .venv/bin/activate
touch pyproject.toml          # Add your project config
uv pip install -e ".[dev]"    # Install in dev mode

# Working with existing projects
git clone https://github.com/org/project
cd project
uv venv
source .venv/bin/activate
uv pip sync requirements.txt  # Or: uv pip install -e ".[dev]"
```

For more details, visit the [UV documentation](https://docs.astral.sh/uv/).
