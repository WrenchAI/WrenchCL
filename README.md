<h1 align="center">Wrench Code Library</h1>

<p align="center">
  <a href="https://github.com/wrenchai/wrenchcl/actions/workflows/run-tests.yml">
    <img src="https://github.com/wrenchai/wrenchcl/actions/workflows/run-tests.yml/badge.svg" alt="Tests">
  </a>
  <a href="https://codecov.io/gh/Kydoimos97/xpytools">
    <img src="https://codecov.io/gh/wrenchai/wrenchcl/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
  </a>
</p>

---

### [ReadTheDocs](https://wrenchcl.readthedocs.io/en/latest)

---

## Description

WrenchCL is a comprehensive library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package aims to streamline the development process by providing robust components for database interactions, cloud storage, and AI-powered functionalities.

**PyPI Link:** [WrenchCL on PyPI](https://pypi.org/project/WrenchCL/)

## Installation

### Basic Installation

To install the core package with minimal dependencies:

```bash
pip install WrenchCL
```

### Optional Dependencies

WrenchCL uses optional dependencies to keep the core package lightweight while providing additional functionality when needed:

#### Color Support (Logger)

```bash
pip install WrenchCL[color]
# Adds: colorama for beautiful terminal colors
```

#### AWS Services

```bash
pip install WrenchCL[aws]
# Adds: boto3, psycopg2-binary, sshtunnel, and AWS service type hints
# Enables: RDS connections, S3 operations, Lambda functions, Secrets Manager
```

#### Distributed Tracing

```bash
pip install WrenchCL[trace]
# Adds: ddtrace for Datadog APM integration
# Enables: Automatic trace correlation in logs
```

#### Development Tools

```bash
pip install WrenchCL[dev]
# Adds: pytest, coverage, pydantic for development and testing
```

#### Complete Installation

```bash
pip install WrenchCL[all]
# Installs all optional dependencies for full functionality
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

Use the `--no-dependencies` flag to reinstall quickly if there are no dependency changes

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall --no-dependencies
```

## Logger

WrenchCL ships a structured, colorized logger available as a singleton:

```python
from WrenchCL import logger
```

### Output modes

| Mode | When to use |
|---|---|
| `terminal` | Local development — colorized, multi-line, syntax-highlighted |
| `json` | Deployed services — single-line JSON with Datadog triad fields |
| `compact` | Space-constrained output — single-line, no color |

```python
logger.configure(mode="json")          # structured JSON
logger.configure(mode="terminal")      # colored terminal output (default)
logger.configure(deployment_mode=True) # deployed terminal — no color, shows context prefix
```

### Logging methods

```python
logger.debug("message")
logger.info("message")
logger.warning("message")
logger.error("message")
logger.critical("message")
logger.exception("message")   # ERROR level + current exception info

logger.data(obj)               # pretty-print dicts, DataFrames, Pydantic models
logger.header("Section title") # formatted section header
```

### Context prefix

In deployed or verbose mode every log line includes a bracket group that identifies the run, request context, and thread:

```
[A3X7K | api-handler | Thread-2 | WrenchCL] INFO    [12:34:56|file.py:10] -> message
```

**Scoped prefix** — the primary way to attach a prefix. Uses `contextvars.ContextVar` so it is per-context (thread and async-task safe) and cleans up automatically:

```python
# Context manager — prefix active only inside the block
with logger.prefix("api-handler"):
    logger.info("handling request")   # [run_id | api-handler | WrenchCL]

logger.info("idle")                   # [run_id | WrenchCL]

# Decorator — prefix active for the entire function or method call
@logger.prefix("PaymentService")
def process_payment(order_id):
    logger.info("processing %s", order_id)
```

**Global prefix** — process-wide fallback, overridden by any scoped prefix:

```python
logger.set_prefix("worker-1")   # set
logger.set_prefix()             # clear
```

**Thread name** — opt-in, off by default:

```python
logger.configure(show_thread_name=True)
# [run_id | prefix | Thread-2 | WrenchCL]
```

**Run ID** — a 5-character uppercase alphanumeric ID generated at startup, refreshed with:

```python
logger.initiate_new_run()
print(logger.run_id)   # e.g. "A3X7K"
```

### Datadog integration

Install the `trace` extra and set `LOG_DD_TRACE=true`:

```bash
pip install WrenchCL[trace]
LOG_DD_TRACE=true python app.py
```

`dd.trace_id` and `dd.span_id` are injected automatically into JSON log records for APM correlation. In AWS Lambda or ECS the logger auto-detects the environment and switches to JSON mode.

### Configuration reference

```python
logger.configure(
    mode="terminal",          # "terminal" | "json" | "compact"
    level="INFO",             # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    deployment_mode=False,    # strip color, activate context prefix
    show_thread_name=False,   # include thread name in context bracket
    prefix=None,              # global prefix string
    color_enabled=True,
    highlight_syntax=True,
    trace_enabled=False,      # Datadog APM correlation
)
```

Temporary overrides:

```python
with logger.temporary(level="DEBUG", mode="compact"):
    logger.debug("verbose output for this block only")
```