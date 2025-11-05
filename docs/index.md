# WrenchCL Documentation

WrenchCL is a comprehensive library for seamless interactions with AWS services, AI models, and enterprise-grade utility tools.

---

## Installation

See **[Installation Guide](installation.md)** for complete setup instructions including optional dependencies.

---

## Core Components

### Logger System

Enterprise-grade structured logging with multi-format output, environment detection, and Datadog integration. Features include terminal colors, JSON formatting, automatic AWS Lambda detection, and APM trace correlation.

- **[Core Interface](logger/core.md)** - Main logging methods and configuration
- **[Configuration](logger/configuration.md)** - State management and environment detection  
- **[Formatters](logger/formatters.md)** - JSON, terminal, and file output formatting
- **[Handler Management](logger/handlers.md)** - Stream, file, and global logger coordination
- **[Message Processing](logger/processing.md)** - Text markup, highlighting, and data visualization
- **[Color System](logger/colors.md)** - Terminal colors and visual themes
- **[Datadog Integration](logger/datadog.md)** - APM trace correlation and structured logging

### AWS Connect

Production-ready AWS service integrations with automatic configuration management, connection pooling, and intelligent error handling. Supports RDS, S3, Lambda, and Secrets Manager with SSH tunneling capabilities.

- **[Client Hub](connect/client-hub.md)** - Centralized AWS client and session management
- **[RDS Gateway](connect/rds.md)** - Database operations with connection pooling and batch processing
- **[S3 Gateway](connect/s3.md)** - Object storage operations with retry logic and type detection
- **[Lambda Utilities](connect/lambda.md)** - Response handling and status code management
- **[Processing Tracker](connect/tracking.md)** - Job lifecycle management with TTL cleanup
- **[Configuration](connect/configuration.md)** - Environment detection and secrets management

### Tools & Utilities

Essential utility functions for data manipulation, file operations, and type safety. All utilities include graceful fallbacks and handle edge cases robustly with minimal dependencies.

- **[Data Manipulation](tools/data.md)** - Null coalescing, type checking, and data standardization
- **[File Operations](tools/files.md)** - Type detection, metadata extraction, and image processing
- **[JSON Processing](tools/json.md)** - Robust parsing, serialization, and malformed JSON handling
- **[Functional Programming](tools/functional.md)** - Maybe monad for safe operations and method chaining

### Decorators

Design pattern implementations following SOLID principles. Provides behavioral, structural, and lifecycle decorators for enhanced functionality and code organization.

- **[Behavioral](decorators/behavioral.md)** - Retry logic and thread synchronization
- **[Structural](decorators/structural.md)** - Singleton pattern enforcement with proper initialization
- **[Lifecycle](decorators/lifecycle.md)** - Deprecation warnings and version management

### Exception System

Comprehensive error handling with intelligent suggestions and hierarchical exception structure. Includes automatic error correction hints and similarity-based suggestions for common mistakes.

- **[Arguments & Validation](exceptions/arguments.md)** - Input validation and type checking errors
- **[Initialization](exceptions/initialization.md)** - Configuration and setup error handling
- **[Runtime](exceptions/runtime.md)** - Security violations and reference errors
- **[Error Suggestions](exceptions/suggestions.md)** - Smart error suggestions and auto-correction

---

## Architecture Overview

WrenchCL follows SOLID principles with clear separation of concerns:

- **Core**: Lightweight logger and essential utilities (no optional deps)
- **Connect**: AWS integrations with automatic configuration
- **Tools**: Utility functions with graceful fallbacks
- **Decorators**: Reusable design patterns
- **Exceptions**: Hierarchical error handling with suggestions

Each module handles its own dependencies and provides meaningful fallbacks when optional packages aren't available.

---

## Contributing

See the [GitHub repository](https://github.com/wrenchai/wrenchcl) for development guidelines and contribution instructions.