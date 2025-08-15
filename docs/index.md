# WrenchCL Documentation

WrenchCL is a comprehensive Python library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package streamlines development by providing robust components for database interactions, cloud storage, and AI-powered functionalities.

## Architecture Overview

WrenchCL is organized into several key modules:

### Core Components

- **Logger** - Advanced structured logging with colorization, JSON output, and Datadog APM integration
- **Connect** - AWS service integrations (RDS, S3, Lambda, Secrets Manager)
- **Decorators** - Utility decorators for retry logic, singleton patterns, and synchronization
- **Tools** - Miscellaneous utility functions for data processing and validation
- **Exceptions** - Comprehensive exception hierarchy with intelligent suggestions

### Optional Dependencies

WrenchCL uses optional dependencies to keep the core package lightweight:

```bash
# Core installation
pip install WrenchCL

# With AWS support
pip install WrenchCL[aws]

# With color support  
pip install WrenchCL[color]

# With tracing support
pip install WrenchCL[trace]

# With development tools
pip install WrenchCL[dev]

# All features
pip install WrenchCL[aws,color,trace,dev]
```

## Quick Start

### Basic Logging

```python
from WrenchCL import logger

# Basic logging
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)

# Structured data logging
logger.data({"user_id": 123, "action": "login"})

# Headers for organization
logger.header("Database Operations")
```

### AWS Services

```python
from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway

# Initialize AWS services
hub = AwsClientHub()
rds = RdsServiceGateway()
s3 = S3ServiceGateway()

# Database operations
results = rds.get_data("SELECT * FROM users WHERE active = %s", (True,))

# S3 operations
s3.upload_file("./data.json", "my-bucket", "data/file.json")
```

### Utility Tools

```python
from WrenchCL.Tools import coalesce, Maybe, typechecker

# Safe value extraction
result = coalesce(None, "", "default_value")  # Returns "default_value"

# Monadic operations
value = Maybe(user_data).get("profile").get("email").out()

# Type validation
typechecker({"name": "John", "age": 30}, {"name": str, "age": int})
```

### Decorators

```python
from WrenchCL.Decorators import Retryable, SingletonClass

@Retryable(max_retries=3, delay=1)
def unreliable_operation():
    # Will retry up to 3 times on failure
    pass

@SingletonClass
class ConfigManager:
    def __init__(self):
        self.config = {}
```

## Configuration

### Environment Variables

WrenchCL respects several environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `COLOR_MODE` | Enable/disable colored output | `true` |
| `LOG_DD_TRACE` | Enable Datadog trace correlation | `false` |
| `AWS_PROFILE` | AWS profile for service connections | `default` |
| `PROJECT_NAME` | Project name for logging context | - |
| `ENV` | Environment name (dev, prod, etc.) | - |

### Logger Configuration

```python
from WrenchCL import logger

# Configure logger behavior
logger.configure(
    mode="json",           # Output format: terminal, json, compact
    level="DEBUG",         # Logging level
    color_enabled=True,    # Enable colors
    trace_enabled=True     # Enable Datadog tracing
)

# Temporary configuration
with logger.temporary(mode="compact", level="ERROR"):
    logger.info("This will be compact and only show errors")
```

## Key Features

### Advanced Logging

- **Multiple Output Modes**: Terminal (colored), JSON (structured), Compact (minimal)
- **Datadog Integration**: Automatic trace correlation and APM support
- **Smart Formatting**: Syntax highlighting for JSON, Python literals, and data structures
- **Exception Suggestions**: Intelligent attribute error suggestions using difflib
- **Thread Safety**: Concurrent logging with proper synchronization

### AWS Integration

- **Unified Configuration**: Single configuration manager for all AWS services
- **Connection Pooling**: Efficient database connection management
- **SSH Tunneling**: Secure database connections through SSH tunnels
- **Error Handling**: Comprehensive retry logic and error reporting
- **Batch Operations**: Optimized bulk data operations

### Development Tools

- **Type Checking**: Runtime type validation with descriptive errors
- **Retry Logic**: Configurable retry patterns for unreliable operations
- **Singleton Pattern**: Thread-safe singleton implementation
- **Data Processing**: JSON parsing, serialization, and transformation utilities

## Best Practices

### Logging

```python
# Use structured logging for better observability
logger.info("User operation completed", extra={
    "user_id": user.id,
    "operation": "profile_update",
    "duration_ms": 150
})

# Use headers to organize log sections
logger.header("Data Processing Pipeline")
logger.info("Starting data validation")
logger.info("Processing 1000 records")
logger.header("Cleanup Operations")
```

### Error Handling

```python
from WrenchCL.Exceptions import InvalidConfigurationException

try:
    # Risky operation
    result = process_data(data)
except InvalidConfigurationException as e:
    logger.error("Configuration error", exc_info=True)
    # Handle gracefully
```

### AWS Operations

```python
# Use connection pooling for high-throughput applications
rds = RdsServiceGateway(multithreaded=True, max_pool_size=20)

# Use batch operations for efficiency
city_state_pairs = [("New York", "NY"), ("Los Angeles", "CA")]
results = rds.batch_city_state_lookup(city_state_pairs)
```

## Performance Considerations

### Memory Usage

- **Lazy Loading**: Optional dependencies loaded only when needed
- **Connection Pooling**: Reuse database connections efficiently
- **Singleton Pattern**: Single instance for configuration managers

### Threading

- **Thread Safety**: All core components are thread-safe
- **Connection Pools**: Separate connections per thread when needed
- **Lock Contention**: Minimal locking with optimized critical sections

## Compatibility

- **Python**: 3.7+
- **AWS Services**: RDS (PostgreSQL), S3, Lambda, Secrets Manager
- **Databases**: PostgreSQL via psycopg2
- **Optional**: colorama, ddtrace, boto3, paramiko

## Migration Guide

### From Standard Logging

```python
# Before
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Message")

# After
from WrenchCL import logger
logger.info("Message")  # Much more features available
```

### From boto3 Direct Usage

```python
# Before
import boto3
s3 = boto3.client('s3')
s3.upload_file('file.txt', 'bucket', 'key')

# After
from WrenchCL.Connect import S3ServiceGateway
s3 = S3ServiceGateway()
s3.upload_file('file.txt', 'bucket', 'key')  # With retries and error handling
```

## Next Steps

- [Core Logger Documentation](logger.md) - Detailed logging features and configuration
- [AWS Services Guide](connect.md) - Complete AWS integration reference
- [Decorators Reference](decorators.md) - Available decorators and patterns
- [Tools Documentation](tools.md) - Utility functions and helpers
- [Exception Handling](exceptions.md) - Exception hierarchy and best practices