<h1 align="center">Wrench Code Library</h1>

<p align="center">
    <img src="https://raw.githubusercontent.com/WrenchAI/WrenchCL/release/resources/img/logo.svg" alt="Logo" style="display: inline-block; vertical-align: middle; width: 90%; max-width: 800px;">
    <br><br>
    <a href="https://pypi.org/project/WrenchCL/" style="text-decoration: none;">
        <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/WrenchCL?logo=pypi&logoColor=green&color=green">
    </a>
    <a href="https://github.com/Kydoimos97" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/Kydoimos97-cb632b?label=Code%20Maintainer" alt="Maintainer" height="20"/>
    </a>
    <a href="https://github.com/WrenchAI/WrenchCL/actions/workflows/publish-to-pypi.yml" style="text-decoration: none;">
        <img alt="GitHub Workflow Status (with event)" src="https://img.shields.io/github/actions/workflow/status/WrenchAI/WrenchCL/publish-to-pypi.yml?event=push&logo=Github&label=Test%20%26%20Publish%20%F0%9F%90%8D%20to%20PyPI%20%F0%9F%93%A6">
    </a>
</p>

## [Read the Docs - Documentation](https://wrenchai.github.io/WrenchCL/)

## Description

WrenchCL is a comprehensive library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package aims to streamline the development process by providing robust components for database interactions, cloud storage, and AI-powered functionalities.


**PyPI Link:** [WrenchCL on PyPI](https://pypi.org/project/WrenchCL/)

## Package Structure

- **_Internal**: Contains internal classes for configuration and SSH tunnel management.
- **Connect**: Provides gateways for AWS RDS and S3 services and the `AWSClientHub`.
- **Decorators**: Utility decorators for retry logic, singleton pattern, and method timing.
- **Models**: _Internal for interacting with OpenAI models.
- **Tools**: Miscellaneous utility tools such as coalescing values, file typing, image encoding, and a custom logger.
- **DataFlow**: Response focused tools to aid in returning values and generating logs based on status codes.

## Installation

To install the package, simply run the following command:

```bash
pip install WrenchCL
```

## Development

To locally develop the plugin, clone the repository locally and make your changes.

Open the console in your working directory; the building command is

```bash
python setup.py sdist bdist_wheel
```

You can then install the package with 

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall
```

Use the `--no-dependencies flag` to reinstall quickly if there are no dependency changes

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall --no-dependencies
```

---

## Logger Documentation

### Overview

The WrenchCL Logger provides a flexible, thread-safe logging system with structured output formats, color support, and integration with cloud environments. It offers multiple output modes, intelligent error suggestions, and extensive configuration options.

### Key Features

- **Multiple Output Modes:** Choose between 'terminal' (human-readable, colored), 'json' (machine-readable for infrastructure), and 'compact' (minimal) formats.
- **Thread Safety:** All operations are thread-safe for concurrent environments.
- **Datadog APM Integration:** Optional trace correlation (trace_id, span_id) for distributed tracing.
- **Intelligent Error Suggestions:** Automatically provides suggestions for typos in attribute names.
- **Syntax Highlighting:** Automatically highlights Python/JSON literals in terminal mode.
- **Environment Awareness:** Auto-detects AWS Lambda, EC2, and other environments.
- **Resource Management:** Proper cleanup of handlers and streams.

### Quick Start

```python
from WrenchCL.Tools import logger

# Basic logging
logger.info("Processing started")
logger.warning("Check this value", value)
logger.error("Something went wrong", exc_info=True)

# Configure for different environments
logger.configure(
    mode="json",       # 'terminal', 'json', or 'compact'
    level="DEBUG",
    trace_enabled=True,
    color_enabled=True,
    verbose=True
)

# Pretty-print structured data
logger.pretty_log({
    "status": "success",
    "count": 42,
    "items": ["apple", "banana", "cherry"]
})

# Add section headers to logs
logger.header("Processing Results")

# Time operations
logger.start_time()
# ... some operation ...
logger.log_time("Processing completed in")
```

### Configuration Options

The logger can be configured in several ways:

```python
# Central configuration
logger.configure(
    mode="terminal",            # Output format ('terminal', 'json', 'compact')
    level="INFO",               # Log level
    color_enabled=True,         # Enable ANSI colors
    verbose=False,              # Include file/line details
    trace_enabled=False         # Include Datadog trace IDs
)

# Individual properties
logger.mode = "compact"         # Set output mode
logger.highlight_syntax = True  # Enable syntax highlighting
logger.setLevel("DEBUG")        # Set log level

# Environment variables
# COLOR_MODE=true|false        # Control color output
# LOG_DD_TRACE=true|false      # Enable Datadog tracing
# PROJECT_NAME, PROJECT_VERSION, ENV  # Add metadata to logs
```

### Context Management

Temporarily change logger configuration:

```python
# Temporarily change configuration
with logger.config_context(mode="compact", level="DEBUG"):
    logger.debug("This will be logged in compact mode at DEBUG level")
    # Outside the context, the logger returns to previous settings
```

### Advanced Features

```python
# Add a rotating file handler
logger.add_rotating_file_handler(
    filename="app.log",
    max_bytes=10485760,  # 10MB
    backup_count=5
)

# Silence third-party loggers
logger.silence_logger("noisy_package")

# Configure global logging
logger.configure_global_stream(level="INFO", silence_others=True)

# Force color in CI/Docker environments
logger.force_color()

# Create a new session ID
logger.initiate_new_run()

# Display current configuration
logger.display_logger_state()

# Proper cleanup on application shutdown
logger.close()
```

### Cloud & Infrastructure Integration

The logger automatically adapts to cloud environments:

- **AWS Lambda/EC2:** Switches to JSON format, disables colors
- **Datadog APM:** Injects trace_id and span_id when available
- **Structured Logging:** JSON format includes standardized fields for log aggregation systems

### Backward Compatibility

The logger maintains compatibility with older versions:

```python
# Legacy methods still work
logger.set_verbose(True)
logger.overwrite_lambda_mode(True)
logger.flow("Processing flow")
logger.context("Execution context")
```