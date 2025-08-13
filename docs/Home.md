# WrenchCL Documentation Wiki

Welcome to the WrenchCL documentation wiki! WrenchCL is a comprehensive Python library for AWS services, data processing, and enterprise application development.

## 🚀 Quick Start

```bash
# Basic installation
pip install WrenchCL

# With optional dependencies
pip install WrenchCL[color,aws,trace,dev]
```

```python

from WrenchCL import logger
from WrenchCL.Connect import AwsClientHub, RdsServiceGateway

# Beautiful logging out of the box
logger.info("Welcome to WrenchCL!")
logger.data({"status": "ready", "modules": ["Connect", "Tools", "Decorators"]})

# AWS services with automatic configuration
hub = AwsClientHub()
s3 = hub.s3
rds = RdsServiceGateway()
```

## 📚 Core Modules

### [🔗 Connect Module](Connect.md)
**AWS Service Integrations**
- **AwsClientHub**: Centralized AWS client management with automatic configuration
- **RdsServiceGateway**: PostgreSQL operations with connection pooling and batch processing
- **S3ServiceGateway**: Comprehensive S3 operations with retry logic
- **Lambda Response Handling**: Standardized response formatting and error codes

**Perfect for:** Cloud applications, data pipelines, serverless functions

### [🛠️ Tools Module](Tools.md)
**Utilities & Data Processing**
- **JSON Processing**: Recursive parsing of complex nested structures
- **Type Validation**: Robust type checking with detailed error messages  
- **File Operations**: Image encoding, type detection, metadata extraction
- **Utility Patterns**: Maybe monad, coalescing, null standardization

**Perfect for:** Data validation, API processing, file handling

### [🎭 Decorators Module](Decorators.md) 
**Production-Ready Patterns**
- **Retryable**: Intelligent retry logic for network and AWS operations
- **SingletonClass**: Thread-safe singleton pattern enforcement
- **Synchronized**: Method-level thread synchronization
- **Deprecated**: Clean deprecation warnings with automatic tracking

**Perfect for:** Resilient applications, thread safety, code evolution

### [⚠️ Exceptions Module](Exceptions.md)
**Error Handling & Flow Control**
- **Rich Exception Hierarchy**: Specialized exceptions for different scenarios
- **GuardedResponseTrigger**: Lambda function control flow mechanism
- **ExceptionSuggestor**: Intelligent suggestions for common mistakes
- **Context-Aware Errors**: Detailed error information for debugging

**Perfect for:** Robust error handling, debugging, user experience

### [📝 Logger](Logger.md)
**Enterprise Logging System**
- **Multiple Output Modes**: Terminal (beautiful), JSON (structured), Compact (minimal)
- **Cloud Integration**: Auto-configures for AWS Lambda, Datadog APM
- **Visual Data Debugging**: Beautiful formatting for complex data structures
- **Performance Optimized**: Pay-for-what-you-use architecture

**Perfect for:** All applications - development to production

---

## 📋 Installation Guide

### **Minimal Installation**
```bash
pip install WrenchCL
```
**Includes:** Core functionality with 5 lightweight dependencies

### **Feature-Specific Installation**
```bash
# Beautiful terminal colors
pip install WrenchCL[color]

# AWS services (S3, RDS, Lambda, Secrets Manager)
pip install WrenchCL[aws]

# Datadog APM integration
pip install WrenchCL[trace] 

# Development tools
pip install WrenchCL[dev]
```

### **Complete Installation**
```bash
pip install WrenchCL[color,aws,trace,dev]
```
**Includes:** All optional features for full functionality

---

## 🏗️ Architecture Principles

WrenchCL is built on solid engineering principles:

### **Modular Design**
- **Optional Dependencies**: Install only what you need
- **Graceful Degradation**: Features degrade gracefully when dependencies are missing
- **Clean Interfaces**: Each module has a focused responsibility

### **Production Ready**
- **Thread Safety**: All components designed for concurrent use
- **Error Recovery**: Intelligent retry logic and detailed error handling
- **Performance**: Optimized for minimal overhead when features are disabled
- **Observability**: Rich logging and debugging capabilities

### **Developer Experience**
- **Type Hints**: Comprehensive type annotations throughout
- **Documentation**: Detailed docstrings and examples
- **Error Messages**: Helpful error messages with suggestions
- **Auto-Configuration**: Smart defaults that work out of the box

---

## 🔧 Configuration

### **Environment Variables**
```bash
# Logging Configuration
COLOR_MODE=true              # Enable/disable colors
LOG_DD_TRACE=true           # Enable Datadog tracing

# AWS Configuration (optional)
AWS_PROFILE=my-profile
REGION_NAME=us-east-1
SECRET_ARN=arn:aws:secretsmanager:...

# Project Metadata (optional)
PROJECT_NAME=my-app
PROJECT_VERSION=1.0.0
ENV=production
```

### **Programmatic Configuration**

```python

from WrenchCL import logger
from WrenchCL.Connect import AwsClientHub

# Configure logger for different environments
if production:
    logger.configure(mode="json", trace_enabled=True)
else:
    logger.configure(mode="terminal", verbose=True)

# Configure AWS with custom settings
hub = AwsClientHub(
        AWS_PROFILE="production",
        REGION_NAME="us-west-2"
        )
```

---

## 📈 Performance & Scalability

### **Efficient by Design**
- **Lazy Loading**: Resources created only when needed
- **Connection Pooling**: Built-in database connection management
- **Caching**: Intelligent caching of AWS clients and configurations
- **Minimal Overhead**: Features can be disabled for zero-cost abstractions

### **Scaling Patterns**
```python
# High-performance database operations
rds = RdsServiceGateway(
    multithreaded=True,
    min_pool_size=5,
    max_pool_size=50
)

# Batch operations for efficiency
rds.update_database(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    payload=list_of_user_tuples  # Efficient batch insert
)

# Configurable retry strategies
@Retryable(max_retries=5, delay=1)  # Fast retry for local services
def local_cache_operation():
    pass

@Retryable(max_retries=3, delay=5)  # Slower retry for external APIs  
def external_api_call():
    pass
```

---

## 🤝 Contributing & Support

### **Getting Help**
- **Documentation**: Start with the module-specific docs above
- **Examples**: Each doc includes real-world usage patterns
- **Type Hints**: Full IDE support with comprehensive type annotations

### **Best Practices**
- **Start Simple**: Begin with basic features and add complexity as needed
- **Use Type Checking**: Enable type checking in your IDE for better development experience
- **Enable Logging**: Use the logger for better visibility into application behavior
- **Handle Errors**: Use the rich exception hierarchy for robust error handling

### **Common Patterns**

```python
# Recommended application setup
from WrenchCL import logger
from WrenchCL.Connect import AwsClientHub
from WrenchCL.Exceptions import GuardedResponseTrigger


def main():
    try:
        # Configure logging first
        logger.configure(mode="terminal", verbose=True)
        logger.info("Application starting")

        # Initialize AWS services
        hub = AwsClientHub()

        # Your application logic
        result = run_application(hub)

        logger.success("Application completed successfully")
        return result

    except Exception as e:
        logger.error("Application failed", e)
        raise


if __name__ == "__main__":
    main()
```

---

## 🔗 Quick Navigation

| Module | Primary Use Case | Key Features |
|--------|------------------|--------------|
| **[Connect](Connect.md)** | AWS Integration | Client management, DB pooling, S3 ops |
| **[Tools](Tools.md)** | Data Processing | JSON parsing, validation, file ops |
| **[Decorators](Decorators.md)** | Resilient Code | Retry logic, singletons, thread safety |
| **[Exceptions](Exceptions.md)** | Error Handling | Rich exceptions, suggestions, flow control |
| **[Logger](Logger.md)** | Observability | Beautiful terminal, JSON output, tracing |

**💡 Pro Tip:** Start with the [Logger documentation](Logger.md) to add beautiful logging to your application, then explore other modules based on your needs.

---

*WrenchCL: Enterprise-grade Python development, simplified.*