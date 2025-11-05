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