# Installation Guide

WrenchCL uses optional dependency groups to keep the core package lightweight while providing enhanced functionality when needed.

---

## Requirements

- **Python**: 3.11 or higher
- **Operating System**: Cross-platform (Windows, macOS, Linux)

---

## Basic Installation

Install the core package with minimal dependencies:

```bash
pip install WrenchCL
```

**Core dependencies included:**
- `python-dotenv` - Environment variable management
- `requests` - HTTP client library
- `filetype` - File type detection
- `ansi2txt` - ANSI escape sequence handling
- `ftfy` - Text encoding fixes

---

## Optional Features

### AWS Integration
For AWS service connectivity and database operations:

```bash
pip install WrenchCL[aws]
```

**Adds:**
- `boto3` & `botocore` - AWS SDK
- `psycopg2` - PostgreSQL adapter  
- `sshtunnel` - SSH tunnel support
- `paramiko` - SSH client library

### Terminal Colors
For enhanced terminal output with colors:

```bash
pip install WrenchCL[color]
```

**Adds:**
- `colorama` - Cross-platform terminal colors

### Datadog Tracing
For APM trace correlation in logs:

```bash
pip install WrenchCL[trace]
```

**Adds:**
- `ddtrace` - Datadog APM tracing

### Documentation
For building documentation locally:

```bash
pip install WrenchCL[mkdocs]
```

**Adds:**
- `mkdocs` - Documentation generator
- `mkdocstrings` - Python docstring integration
- `mkdocs-material` - Material theme
- Additional documentation plugins

---

## Combined Installations

### All Runtime Features
Install all production-ready features:

```bash
pip install WrenchCL[all]
```

Equivalent to: `pip install WrenchCL[aws,trace,color]`

### Development Setup
Install everything including development tools:

```bash
pip install WrenchCL[dev-all]
```

**Additional development tools:**
- `pytest` - Testing framework
- `mypy` - Type checking
- `ruff` - Code formatting and linting
- `coverage` - Code coverage analysis
- `pydantic` - Data validation
- `pandas` - Data manipulation

---

## Installation Examples

### Production Environment
```bash
# AWS Lambda or containerized deployment
pip install WrenchCL[aws,trace]
```

### Local Development
```bash
# Full development environment
pip install WrenchCL[dev-all]
```

### CI/CD Pipeline
```bash
# Testing and linting
pip install WrenchCL[dev]
```

### Documentation Building
```bash
# Documentation generation only
pip install WrenchCL[mkdocs]
```

---

## Verification

Verify your installation:

```python
import WrenchCL
from WrenchCL import logger

logger.info("WrenchCL installed successfully!")
print(f"Version: {WrenchCL.__version__}")
```

---

## Troubleshooting

### Common Issues

**Import errors for optional features:**
```bash
# If you see "ImportError" for AWS features
pip install WrenchCL[aws]

# If you see "ImportError" for color features  
pip install WrenchCL[color]
```

**PostgreSQL adapter issues:**
```bash
# On some systems, you may need system dependencies
# Ubuntu/Debian:
sudo apt-get install libpq-dev python3-dev

# macOS:
brew install postgresql
```

**SSH tunnel connectivity:**
```bash
# Ensure SSH key permissions
chmod 600 ~/.ssh/your_key.pem
```

---

## Links

- **PyPI**: https://pypi.org/project/WrenchCL/
- **GitHub**: https://github.com/WrenchAI/WrenchCL
- **Documentation**: https://wrenchcl.readthedocs.io/
- **Issues**: https://github.com/WrenchAI/WrenchCL/issues