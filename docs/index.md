# WrenchCL Documentation

WrenchCL is a Python library focused on advanced logging with optional AWS integrations and utility tools.

## Quick Start

```bash
# Core installation
pip install WrenchCL

# With AWS support (requires additional dependencies)
pip install WrenchCL[aws]
```

## Basic Usage

```python
from WrenchCL import logger

# Basic logging
logger.info("Application started")
logger.error("Something failed", exc_info=True)

# Structured data logging
logger.data({"user_id": 123, "action": "login"})

# Organize with headers
logger.header("Database Operations")
```

## Package Structure

WrenchCL exports only the logger from the root package. Other modules must be imported explicitly:

```python
# Core logger (always available)
from WrenchCL import logger

# Optional modules (may require additional dependencies)
from WrenchCL.Tools import coalesce, Maybe
from WrenchCL.Decorators import Retryable, SingletonClass
from WrenchCL.Exceptions import InvalidConfigurationException

# AWS modules (require 'aws' extra dependencies)
from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway
```

## Core Components

### Logger

Advanced structured logging with colorization, JSON output, and Datadog integration.

### Tools (WrenchCL.Tools)

- `coalesce()` - Return first non-None value
- `Maybe` - Safe nested attribute access
- `typechecker()` - Runtime type validation
- JSON parsing and serialization utilities
- File type detection and image processing

### Decorators (WrenchCL.Decorators)

- `@Retryable` - Automatic retry logic
- `@SingletonClass` - Thread-safe singleton pattern
- `@Synchronized` - Method synchronization
- `@Deprecated` - Deprecation warnings

### Connect (WrenchCL.Connect) - Requires AWS Dependencies

- `AwsClientHub` - Unified AWS client management
- `RdsServiceGateway` - PostgreSQL database operations
- `S3ServiceGateway` - S3 storage operations
- Lambda utilities

### Exceptions (WrenchCL.Exceptions)

Structured exception hierarchy with intelligent error suggestions.

## Configuration

The logger can be configured via environment variables:

```bash
export COLOR_MODE=true          # Enable colors
export LOG_DD_TRACE=true        # Enable Datadog tracing
export PROJECT_NAME=my-app      # Project context
export ENV=production           # Environment
```

Or programmatically:

```python
logger.configure(
        mode="json",  # terminal, json, or compact
        level="INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        color_enabled=True
        )
```

## AWS Dependencies

AWS functionality requires additional packages:

```bash
pip install boto3 psycopg2-binary paramiko sshtunnel
# or
pip install WrenchCL[aws]
```

If AWS dependencies are missing, importing Connect modules will raise helpful error messages.

## Next Steps

- [Logger Documentation](logger.md) - Core logging features
- [Tools Documentation](tools.md) - Utility functions
- [AWS Connect Guide](connect.md) - AWS service integration
- [Decorators Reference](decorators.md) - Available decorators
- [Exception Handling](exceptions.md) - Exception hierarchy