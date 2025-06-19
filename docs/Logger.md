## Logger Documentation

### Overview

The WrenchCL Logger provides a production-ready, thread-safe logging system with beautiful terminal output, structured JSON logging for cloud environments, and intelligent performance optimization. Built as an enhancement layer over Python's standard logging module, it provides powerful features while maintaining full compatibility and escape hatches to the underlying infrastructure.

### Key Features

- **Minimal Core Dependencies:** Only 5 lightweight required packages - optional features use optional dependencies
- **Multiple Output Modes:** Choose between 'terminal' (beautiful colored output), 'json' (structured logging for infrastructure), and 'compact' (minimal overhead) formats.
- **Performance by Design:** Pay-for-what-you-use architecture with configurable feature overhead.
- **Cloud Native:** Auto-detects and optimizes for AWS Lambda, EC2, and containerized environments.
- **Thread Safety:** All operations are thread-safe for concurrent applications.
- **Optional Integrations:** Modular dependencies for colors (`colorama`), tracing (`ddtrace`), AWS services (`boto3`), etc.
- **Smart Exception Enhancement:** Automatically provides suggestions for common errors like typos in attribute names.
- **Syntax Highlighting:** Configurable highlighting of Python/JSON literals and data structures (requires `colorama`).
- **Stdlib Compatible:** Enhances rather than replaces Python's logging module, with full access to underlying logger.
- **Visual Data Debugging:** Beautiful formatting for complex data structures, nested JSON, and DataFrames.

### Quick Start

```python
from WrenchCL.Tools import logger

# Basic logging - familiar API
logger.info("Processing started")
logger.warning("Check this value", some_variable)
logger.error("Operation failed", exception_obj, header="Critical Error")

# Beautiful data visualization
logger.data({
    "user": {"id": 123, "name": "Alice"},
    "results": [{"score": 95}, {"score": 87}],
    "metadata": {"timestamp": "2025-01-28", "version": "2.1"}
})

# Compact data logging (uses pprint)
logger.cdata(large_data_structure)

# Add visual headers
logger.header("Processing Results")
logger.info("All operations completed successfully")

# Time operations
logger.start_time()
# ... your code here ...
logger.log_time("Database migration completed")
```

### Configuration & Modes

Configure the logger for different environments and use cases:

```python
# Development: Rich visual output
logger.configure(
    mode="terminal",
    color_enabled=True,
    highlight_syntax=True,
    verbose=True
)

# Production: Structured JSON logging
logger.configure(
    mode="json",
    deployment_mode=True,
    trace_enabled=True
)

# CI/CD: Minimal overhead
logger.configure(
    mode="compact",
    color_enabled=False,
    highlight_syntax=False
)

# Performance critical: Disable expensive features
logger.configure(
    color_enabled=False,
    highlight_syntax=False
)
```

### Advanced Features

#### File Logging with Rotation
```python
# Add rotating file handler
logger.enable_file_logging(
    filename="app.log",
    max_bytes=10485760,  # 10MB
    backup_count=5
)
```

#### Global Logger Management
```python
# Take control of application-wide logging
logger.attach_global_stream(level="INFO", silence_others=True)

# Silence specific noisy loggers
logger.silence_logger("urllib3.connectionpool")
logger.silence_logger("boto3.session")

# Configure specific logger levels
logger.set_named_logger_level("my_module", "DEBUG")
```

#### Context Management
```python
# Temporarily change configuration
with logger.temporary(mode="json", level="DEBUG", color_enabled=False):
    logger.debug("This will be JSON formatted at DEBUG level")
    # Configuration automatically reverts after context
```

#### Direct Access to Standard Logging
```python
# Access underlying logging.Logger instance
stdlib_logger = logger.logger_instance

# Add any standard logging handler
logger.add_new_handler(
    logging.handlers.SysLogHandler,
    level="ERROR"
)

# Full compatibility with logging ecosystem
import logging
logging.getLogger("my_app").addHandler(logger.handlers[0])
```

### Environment Integration

The logger automatically adapts to deployment environments:

#### Cloud Environments
- **AWS Lambda/EC2:** Auto-switches to JSON mode, disables colors
- **Container Detection:** Optimizes for containerized deployments
- **Environment Variables:** Respects `COLOR_MODE`, `LOG_DD_TRACE`, `ENV`, `PROJECT_NAME`

#### Datadog APM Integration
```python
# Enable tracing (requires: pip install WrenchCL[trace])
logger.configure(trace_enabled=True)
# Automatically includes trace_id and span_id in JSON logs
```

#### Force Colors in CI/Docker
```python
# Override environment detection (requires: pip install WrenchCL[color])
logger.force_markup()  # Enables colors even in non-TTY environments
```

### Data Visualization

#### Structured Data Logging
```python
# Clean JSON formatting (default)
logger.data({
    "nested": {"deeply": {"structured": "data"}},
    "list": [1, 2, 3]
})

# Compact Python formatting
logger.cdata(complex_data_structure)

# Custom formatting options
logger.data(data, indent=4, compact=False)
```

#### DataFrame Support
```python
import pandas as pd
df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
logger.data(df)  # Beautifully formatted table output
```

### Performance Optimization

The logger is designed for minimal overhead when features are disabled:

```python
# Benchmark mode - minimal processing
logger.configure(
    mode="compact",
    color_enabled=False,
    highlight_syntax=False,
    verbose=False
)

# Feature-specific control
logger.highlight_syntax = False  # Disable regex processing
logger.configure(color_enabled=False)  # Disable ANSI processing
```

### Utility Methods

```python
# Session management
logger.initiate_new_run()  # Generate new run ID

# Configuration inspection
logger.display_logger_state()  # Show current configuration
print(logger.logger_state)     # Access state as dict

# Resource cleanup
logger.flush_handlers()  # Flush all output
logger.close()          # Clean shutdown

# Color customization
logger.update_color_presets(INFO="BLUE", ERROR="MAGENTA")
```

### Migration from Legacy APIs

If upgrading from older versions:

```python
# Old (deprecated)          # New (recommended)
logger.__pretty_log(data)   # logger.data(data)
logger.pretty_log(data)     # logger.data(data, compact=False)
                           # logger.cdata(data)  # for compact pprint

# Legacy methods still supported for backward compatibility
logger.set_verbose(True)    # Still works
logger.overwrite_lambda_mode(True)  # Still works
```

### Best Practices

1. **Configure once at startup:**
   ```python
   logger.configure(mode="json" if production else "terminal")
   ```

2. **Use appropriate log levels:**
   ```python
   logger.debug("Detailed debugging info")
   logger.info("General information") 
   logger.warning("Something needs attention")
   logger.error("An error occurred", exception)
   ```

3. **Leverage data logging for complex structures:**
   ```python
   logger.data(api_response)  # Better than str(api_response)
   ```

4. **Clean up resources:**
   ```python
   # In application shutdown
   logger.close()
   ```

5. **Use context managers for temporary changes:**
   ```python
   with logger.temporary(level="DEBUG"):
       # Detailed logging only in this block
   ```