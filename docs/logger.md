# Core Logger

The WrenchCL logger is a powerful, structured logging system with advanced features including colorization, JSON output, Datadog APM integration, and intelligent error handling.

## Overview

::: WrenchCL.cLogger
    options:
      show_source: false
      heading_level: 3
      members:
        - configure
        - reinitialize
        - setLevel
        - info
        - debug
        - warning
        - error
        - critical
        - exception
        - header
        - data
        - enable_color
        - disable_color
        - force_markup
        - temporary

## Quick Start

### Basic Usage

```python
from WrenchCL import logger

# Standard logging levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")

# Exception logging with traceback
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
```

### Structured Data Logging

```python
# Log complex data structures
user_data = {
    "user_id": 12345,
    "email": "user@example.com",
    "last_login": "2024-01-15T10:30:00Z"
}

logger.data(user_data)  # Pretty-printed with syntax highlighting

# Compact data logging
logger.cdata(large_dataset)  # More compact format
```

### Headers and Organization

```python
# Add visual headers to organize log sections
logger.header("Database Migration")
logger.info("Starting migration process")
logger.info("Migrating user table")
logger.header("Post-Migration Validation")
logger.info("Validating data integrity")
```

## Configuration

### Output Modes

The logger supports three output modes:

#### Terminal Mode (Default)
Colorized output optimized for development and debugging.

```python
logger.configure(mode="terminal")
```

#### JSON Mode
Structured JSON output for production and log aggregation systems.

```python
logger.configure(mode="json")
```

#### Compact Mode
Minimal single-line output for space-constrained environments.

```python
logger.configure(mode="compact")
```

### Configuration Options

```python
logger.configure(
    mode="terminal",          # Output format
    level="INFO",            # Logging level
    color_enabled=True,      # Enable colors
    highlight_syntax=True,   # Syntax highlighting
    verbose=True,           # Show detailed information
    trace_enabled=False,    # Datadog trace correlation
    deployment_mode=False   # Production mode settings
)
```

### Environment-Based Configuration

The logger automatically detects deployment environments:

| Environment | Auto-Configuration |
|-------------|-------------------|
| AWS Lambda | `mode="json"`, `color_enabled=False`, `deployed=True` |
| AWS ECS/EC2 | `deployed=True`, `color_enabled=False` |
| Local Development | `mode="terminal"`, `color_enabled=True` |

Override with environment variables:

```bash
# Force colors in any environment
export COLOR_MODE=true

# Enable Datadog tracing
export LOG_DD_TRACE=true

# Set project context
export PROJECT_NAME=my-app
export ENV=production
export PROJECT_VERSION=1.2.3
```

## Advanced Features

### Temporary Configuration

Use context managers for temporary configuration changes:

```python
# Normal logging
logger.info("Standard log message")

# Temporary JSON mode
with logger.temporary(mode="json", level="DEBUG"):
    logger.info("This will be JSON formatted")
    logger.debug("Debug info in JSON")

# Back to normal
logger.info("Standard format again")
```

### Global Logger Management

Manage the entire Python logging ecosystem:

```python
# Attach global stream to capture all Python logs
logger.attach_global_stream(level="INFO", silence_others=True)

# Configure specific loggers
logger.set_named_logger_level("requests", "WARNING")
logger.set_named_logger_level("boto3", "ERROR")

# Silence noisy loggers
logger.silence_logger("urllib3.connectionpool")

# View active loggers
print(logger.active_loggers)
```

### File Logging

```python
# Add rotating file handler
logger.enable_file_logging(
    filename="app.log",
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5,
    level="INFO"
)

# Multiple handlers with different levels
logger.add_new_handler(
    handler_cls=logging.StreamHandler,
    stream=sys.stderr,
    level="ERROR"
)
```

### Datadog Integration

```python
# Enable Datadog trace correlation
logger.configure(trace_enabled=True)

# Traces will include correlation IDs
logger.info("Processing request")  # Includes dd.trace_id and dd.span_id
```

## Color and Markup

### Color Control

```python
# Enable colors explicitly
presets = logger.enable_color()

# Disable colors
logger.disable_color()

# Force colors even in non-TTY environments
logger.force_markup()
```

### Syntax Highlighting

The logger automatically highlights various elements:

- **JSON/Python literals**: `true`, `false`, `null`, numbers
- **UUIDs**: Automatic detection and highlighting  
- **Brackets and braces**: `{}`, `[]`, `()`
- **Log levels**: `ERROR`, `WARNING`, etc.
- **Data structures**: Keys, values, syntax elements

Example output:
```
INFO     -> User data: {
    "user_id": 12345,
    "active": true,
    "balance": 150.75,
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Performance and Threading

### Thread Safety

The logger is fully thread-safe:

```python
import threading
from WrenchCL import logger

def worker(thread_id):
    logger.info(f"Worker {thread_id} starting")
    # Safe concurrent logging
    logger.data({"thread": thread_id, "status": "processing"})

# Multiple threads can log safely
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

### Performance Monitoring

```python
# Built-in timing utilities
logger.start_time()
process_large_dataset()
logger.log_time("Dataset processing completed")

# Custom timing context
with logger.temporary(verbose=True):
    logger.info("Detailed operation logs")
```

## Log Formatting Examples

### Terminal Mode
```
🔧 MYAPP : PROD | R-A1234B | [10:30:15|main.py:process:42] INFO     -> Processing user request
{
    "user_id": 12345,
    "action": "profile_update"
}
```

### JSON Mode
```json
{
  "level": "INFO",
  "message": "Processing user request",
  "source": {
    "module": "main",
    "function": "process", 
    "line": 42
  },
  "log_info": {
    "logger": "WrenchCL",
    "timestamp": "2024-01-15T10:30:15Z"
  },
  "trace": {
    "dd.service": "myapp",
    "dd.env": "prod", 
    "dd.version": "1.2.3"
  }
}
```

### Compact Mode
```
INFO main.py:process:42 -> Processing user request {"user_id": 12345, "action": "profile_update"}
```

## Error Handling and Suggestions

### Intelligent Exception Suggestions

The logger provides intelligent suggestions for common errors:

```python
class User:
    def __init__(self):
        self.username = "john"

user = User()
try:
    print(user.usernme)  # Typo
except AttributeError as e:
    logger.error("Attribute error", exc_info=True)
    # Output: AttributeError: 'User' object has no attribute 'usernme'
    #         Did you mean: username?
```

### Exception Context

```python
try:
    process_data(invalid_data)
except Exception as e:
    logger.error("Data processing failed", exc_info=True)
    # Automatically captures:
    # - Exception type and message
    # - Full stack trace
    # - Suggested corrections
    # - Context information
```

## Integration Examples

### Flask Application

```python
from flask import Flask
from WrenchCL import logger

app = Flask(__name__)

# Configure for web application
logger.configure(mode="json", level="INFO")
logger.attach_global_stream(level="WARNING")

@app.before_request
def log_request():
    logger.info("Request received", extra={
        "method": request.method,
        "path": request.path,
        "user_agent": request.user_agent.string
    })

@app.errorhandler(500)
def handle_error(error):
    logger.error("Internal server error", exc_info=True)
    return "Internal Server Error", 500
```

### AWS Lambda

```python
import json
from WrenchCL import logger

# Auto-configured for Lambda environment
def lambda_handler(event, context):
    logger.info("Lambda function started", extra={
        "request_id": context.aws_request_id,
        "function_name": context.function_name
    })
    
    try:
        result = process_event(event)
        logger.info("Processing completed successfully")
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        logger.error("Lambda execution failed", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Data Processing Pipeline

```python
from WrenchCL import logger

def process_pipeline(data_source):
    logger.header("Data Processing Pipeline")
    
    with logger.temporary(verbose=True):
        logger.info(f"Starting pipeline with {len(data_source)} records")
        
        # Validation phase
        logger.header("Data Validation", size=40, compact=True)
        valid_records = validate_data(data_source)
        logger.info(f"Validated {len(valid_records)} records")
        
        # Processing phase
        logger.header("Data Transformation", size=40, compact=True)
        processed = transform_data(valid_records)
        logger.data(processed[:5])  # Show sample
        
        # Output phase
        logger.header("Data Output", size=40, compact=True)
        save_results(processed)
        logger.info("Pipeline completed successfully")
```

## Best Practices

### Structured Logging

```python
# Good: Structured with context
logger.info("User login successful", extra={
    "user_id": user.id,
    "login_method": "oauth",
    "duration_ms": 150
})

# Avoid: Unstructured strings
logger.info(f"User {user.id} logged in via oauth in 150ms")
```

### Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug("Cache hit for key: user_profile_123")

# INFO: General operational information
logger.info("User profile updated successfully")

# WARNING: Something unexpected but not an error
logger.warning("API rate limit approaching threshold")

# ERROR: Error condition but application continues
logger.error("Failed to send notification email", exc_info=True)

# CRITICAL: Serious error, application may abort
logger.critical("Database connection lost")
```

### Performance Considerations

```python
# Efficient: Use lazy evaluation
logger.debug("Processing data: %s", expensive_operation())

# Less efficient: Always evaluates
logger.debug(f"Processing data: {expensive_operation()}")

# Good: Check level before expensive operations
if logger.level <= logging.DEBUG:
    complex_debug_info = generate_debug_data()
    logger.debug("Debug info", extra=complex_debug_info)
```

### Resource Management

```python
try:
    # Application code
    run_application()
finally:
    # Ensure proper cleanup
    logger.flush_handlers()
    logger.close()
```

## Troubleshooting

### Common Issues

**Colors not showing in production:**
```python
# Check color settings
print(f"Color enabled: {logger.config_manager.current_state.color_enabled}")
print(f"Force markup: {logger.config_manager.current_state.force_markup}")

# Force enable if needed
logger.force_markup()
```

**Logs not appearing:**
```python
# Check log level
print(f"Current level: {logger.level}")

# Check handlers
print(f"Handlers: {[type(h).__name__ for h in logger.handlers]}")

# Enable debug mode
logger.configure(level="DEBUG", verbose=True)
```

**JSON format issues:**
```python
# Verify JSON mode
logger.configure(mode="json")
logger.display_logger_state()
```

### Debug Mode

```python
# Enable comprehensive debugging
logger.configure(
    mode="terminal",
    level="DEBUG", 
    verbose=True,
    color_enabled=True
)

# Show current configuration
logger.display_logger_state()
```