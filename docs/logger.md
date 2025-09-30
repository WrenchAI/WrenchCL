# Logger

WrenchCL's core logger provides structured logging with colorization, JSON output, and Datadog integration.

## Basic Usage

```python
from WrenchCL import logger

# Standard log levels
logger.debug("Debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
logger.critical("Critical failure")

# Data logging with formatting
logger.data({"user_id": 123, "status": "active"})

# Headers for organization  
logger.header("Processing Phase")
```

## Configuration

### Output Modes

```python
# Terminal mode (default) - colored output
logger.configure(mode="terminal")

# JSON mode - structured output for production
logger.configure(mode="json")

# Compact mode - single-line output
logger.configure(mode="compact")
```

### Configuration Options

```python
logger.configure(
        mode="terminal",  # Output format
        level="INFO",  # Log level
        color_enabled=True,  # Enable colors
        highlight_syntax=True,  # Syntax highlighting
        verbose=True,  # Show detailed info
        trace_enabled=False,  # Datadog tracing
        deployment_mode=False  # Production settings
        )
```

### Environment Variables

```bash
export COLOR_MODE=true          # Force colors
export LOG_DD_TRACE=true        # Enable Datadog traces
export PROJECT_NAME=my-app      # Project context
export ENV=production           # Environment name
export PROJECT_VERSION=1.0.0   # Version info
```

## Advanced Features

### Temporary Configuration

```python
# Temporarily change settings
with logger.temporary(mode="json", level="DEBUG", deployed=True):
    logger.info("This will be JSON formatted")

# Available parameters: level, mode, color_enabled, verbose, 
# trace_enabled, highlight_syntax, deployed
with logger.temporary(color_enabled=False, verbose=True):
    logger.info("No colors, verbose mode")

# Back to original settings
logger.info("Normal format")
```

### Global Logger Management

```python
# Capture all Python logging
logger.attach_global_stream(level="INFO", silence_others=True)

# Configure specific loggers
logger.set_named_logger_level("requests", "WARNING")
logger.silence_logger("urllib3")

# View active loggers
print(logger.active_loggers)
```

### File Logging

```python
# Add rotating file handler
logger.enable_file_logging(
        filename="app.log",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5
        )
```

### Colors and Markup

```python
# Control colors
logger.enable_color()
logger.disable_color()
logger.force_markup()  # Force colors even in non-TTY

# Check current state
print(f"Colors enabled: {logger.state_manager.current_state.color_enabled}")
```

## Properties and State

```python
# Logger information
print(logger.level)  # Current log level
print(logger.mode)  # Current output mode  
print(logger.highlight_syntax)  # Syntax highlighting enabled
print(logger.state)  # Full configuration state
print(logger.handlers)  # Active handlers
print(logger.active_loggers)  # All active loggers
```

## Real Examples

### Development Setup

```python
from WrenchCL import logger

# Configure for development
logger.configure(
        mode="terminal",
        level="DEBUG",
        color_enabled=True,
        verbose=True
        )

logger.header("Application Startup")
logger.info("Loading configuration")
logger.debug("Config details", extra={"config_file": "app.conf"})
```

### Production Setup

```python
# Auto-configures in AWS Lambda/ECS environments
# Or configure manually:
logger.configure(
        mode="json",
        level="INFO",
        trace_enabled=True,  # For Datadog APM
        deployment_mode=True
        )
```

### Error Handling with Suggestions

```python
class User:
    def __init__(self):
        self.username = "john"


user = User()
try:
    print(user.usernme)  # Typo
except AttributeError as e:
    logger.error("Attribute error", exc_info=True)
    # Output includes: "Did you mean: username?"
```

## Performance and Threading

The logger is fully thread-safe and handles concurrent access properly:

```python
import threading


def worker(worker_id):
    logger.info(f"Worker {worker_id} processing")
    logger.data({"worker": worker_id, "status": "complete"})


# Safe concurrent logging
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

## Output Examples

### Terminal Mode

```
INFO     -> Processing request {"user_id": 123}
ERROR    -> Database connection failed
  AttributeError: 'Connection' object has no attribute 'execut'
    Did you mean: execute?
```

### JSON Mode

```json
{
  "level": "INFO",
  "message": "Processing request",
  "source": {
    "module": "main",
    "function": "process",
    "line": 42
  },
  "log_info": {
    "timestamp": "2024-01-15T10:30:15Z"
  },
  "trace": {
    "dd.service": "myapp",
    "dd.env": "prod"
  }
}
```

### Compact Mode

```
INFO main.py:42 -> Processing request {"user_id": 123}
```