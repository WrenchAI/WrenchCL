<h1 align="center">Wrench Code Library</h1>

<p align="center">
    <img src="https://raw.githubusercontent.com/WrenchAI/WrenchCL/release/resources/img/logo.svg" alt="Logo" style="display: inline-block; vertical-align: middle; width: 90%; max-width: 800px;">
    <br><br>
    <a href="https://pypi.org/project/WrenchCL/" style="text-decoration: none;">
        <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/WrenchCL?logo=pypi&logoColor=green&color=green">
    </a>
    <a href="https://github.com/Kydoimos97" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/Kydoimos97-cb632b?label=Code%20Maintainer" alt="Maintainer" height="20"/>
    </a>
    <a href="https://github.com/WrenchAI/WrenchCL/actions/workflows/publish-to-pypi.yml" style="text-decoration: none;">
        <img alt="GitHub Workflow Status (with event)" src="https://img.shields.io/github/actions/workflow/status/WrenchAI/WrenchCL/publish-to-pypi.yml?event=push&logo=Github&label=Test%20%26%20Publish%20%F0%9F%90%8D%20to%20PyPI%20%F0%9F%93%A6">
    </a>
</p>

## [Read the Docs - Documentation](https://wrenchai.github.io/WrenchCL/)

## Description

WrenchCL is a comprehensive library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package aims to streamline the development process by providing robust components for database interactions, cloud storage, and AI-powered functionalities.


**PyPI Link:** [WrenchCL on PyPI](https://pypi.org/project/WrenchCL/)

## Package Structure

- **_Internal**: Contains internal classes for configuration and SSH tunnel management.
- **Connect**: Provides gateways for AWS RDS and S3 services and the `AWSClientHub`.
- **Decorators**: Utility decorators for retry logic, singleton pattern, and method timing.
- **Models**: _Internal for interacting with OpenAI models.
- **Tools**: Miscellaneous utility tools such as coalescing values, file typing, image encoding, and a custom logger.
- **DataFlow**: Response focused tools to aid in returning values and generating logs based on status codes.

## Installation

To install the package, simply run the following command:

```bash
pip install WrenchCL
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

Use the `--no-dependencies flag` to reinstall quickly if there are no dependency changes

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall --no-dependencies
```
## Logger Documentation

Certainly! Below is comprehensive documentation for the `BaseLogger` and `Logger` classes, detailing the various settings, modes, and methods available. This guide will help new users understand how to configure and utilize the logger effectively.

---

## Logger Documentation

Here's the updated Logger documentation with added clarifications and adjustments based on the code provided:

---

## Logger Documentation

### Overview

The `BaseLogger` class provides a flexible and powerful logging system that supports console and file logging, colored output, custom log levels, and various configurations tailored to different environments, such as AWS Lambda. The `Logger` class extends `BaseLogger`, adding convenience methods for logging messages with different severity levels and modes.

### Key Features

- **Console and File Logging:** Logs can be sent to the console and optionally to a file.
- **Custom Log Levels:** Supports standard log levels (INFO, DEBUG, ERROR, etc.) and custom levels (CONTEXT, HDL_WARN, FLOW, etc.).
- **Colored Output:** When `colorama` is available, logs can be displayed with colors for enhanced readability; otherwise, non-colored output is used.
- **Traceback Logging:** Supports detailed stack traces for errors and custom log formatting options.
- **Lambda Awareness:** Configurations adjust automatically when running on AWS Lambda or can be manually overridden.
- **Verbose and Non-Verbose Modes:** Toggle between detailed logging and more concise outputs.
- **Session Management:** Easily generate new run IDs to differentiate log sessions.

---

### BaseLogger Class

#### Constructor

```python
def __init__(self, level: str = 'INFO') -> None
```

- **`level`**: Sets the initial logging level. Acceptable values include 'DEBUG', 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'.

#### Methods

1. **`log_file(path: str) -> None`**
   - Configures the logger to dump logs to a specified file while also continuing to log to the console.
   - **`path`**: The path to the file where logs should be saved.

2. **`release_log_file() -> None`**
   - Stops logging to the file and releases the resources associated with the file handler.

3. **`suppress_package_logger(package_name: str, level: int = logging.CRITICAL) -> None`**
   - Suppresses logging for a specific package, setting its log level to the specified level. Adds a `NullHandler` to prevent propagation to the root logger if none exists.
   - **`package_name`**: The name of the package logger to suppress.
   - **`level`**: The logging level to set for the package logger. Defaults to `CRITICAL`.

4. **`setLevel(level: str) -> None`**
   - Changes the reporting level of the logger and updates the levels of existing console and file handlers.
   - **`level`**: The desired logging level as a string (e.g., 'DEBUG', 'INFO', etc.).

5. **`set_verbose(verbose: bool) -> None`**
   - Toggles between verbose and non-verbose mode.
   - **`verbose`**: If `True`, enables verbose logging with file, function, and line details; otherwise, switches to a concise format.

6. **`set_global_traceback(setting: bool) -> None`**
   - Enables or disables global stack trace logging for all error logs.
   - **`setting`**: If `True`, forces stack traces to be included in error logs.

7. **`revertLoggingLevel() -> None`**
   - Reverts the logging level to the previously set level. If no previous level is saved, it defaults to `INFO`.

8. **`overwrite_lambda_mode(setting: bool) -> None`**
   - Manually sets whether the logger should behave as if it's running on AWS Lambda, affecting logging format and settings.
   - **`setting`**: If `True`, forces the logger to operate in Lambda mode.

9. **`initiate_new_run() -> None`**
   - Generates a new run ID, useful for differentiating log sessions.

---

### Logger Class

The `Logger` class extends `BaseLogger`, adding specialized methods for logging different levels of messages. Each method allows for optional stack trace inclusion and compact formatting.

#### Key Methods

1. **`info(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None`**
   - Logs an informational message.
   - **`stack_info`**: If `True`, includes stack trace information.
   - **`compact`**: If `True`, formats the log message compactly.

2. **`flow(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None`**
   - Logs a message at the FLOW level (custom).

3. **`context(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None`**
   - Logs a contextual message at the CONTEXT level (custom).

4. **`warning(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None`**
   - Logs a warning message.

5. **`error(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None`**
   - Logs an error message, including stack traces if an exception is detected among the arguments. If an exception is present, `stack_info` is automatically set to `True`.

6. **`critical(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None`**
   - Logs a critical message indicating severe issues.

7. **`debug(*args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None`**
   - Logs debugging information.

8. **`data(data: Any, object_name: Optional[str] = None, content: Optional[bool] = True, wrap_length: Optional[int] = None, max_rows: Optional[int] = None, stack_info: Optional[bool] = False, indent: Optional[int] = 4) -> None`**
   - Formats and logs structured data, such as dictionaries or DataFrames. Supports wrapping and formatting based on verbosity settings.

9. **`start_time() -> None`**
   - Starts a timer for tracking elapsed time between log calls.

10. **`log_time(message: str = "Elapsed time", format: str = "seconds", stack_info: Optional[bool] = False) -> None`**
    - Logs the elapsed time since the timer was started, checking if the timer was initiated correctly.
    - **`format`**: Specifies the time format, either "seconds" or "formatted".

11. **`header(text: str, size: int = 80, newline: bool = True) -> None`**
    - Logs a formatted header with optional color and centering using dashes (`-`).

---

### Logging Modes and Settings

1. **Verbose vs. Non-Verbose Mode:**
   - Use `set_verbose(True)` to enable detailed log messages with file, function, and line details.
   - Use `set_verbose(False)` for concise log messages, primarily showing level, timestamp, and message.

2. **AWS Lambda Mode:**
   - Detected automatically when running in AWS Lambda (`'AWS_LAMBDA_FUNCTION_NAME' in os.environ`).
   - Can be manually overridden using `overwrite_lambda_mode(True/False)`.

3. **Logging Levels:**
   - Supports standard levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL.
   - Custom levels: CONTEXT, HDL_WARN, DATA, FLOW, HDL_ERR, and RCV_ERR, with specialized uses. Custom levels are integrated using `logging.addLevelName`.

4. **File Logging:**
   - Easily configured with `log_file(path)`. Logs are written to the specified file and printed to the console.
   - Stopped and resources released with `release_log_file()`.

5. **Package-Specific Log Suppression:**
   - Suppress noisy package loggers using `suppress_package_logger('package_name')`. Adds a `NullHandler` if none exist.

6. **Session Management:**
   - Use `initiate_new_run()` to generate a new run ID, useful for differentiating log sessions.

7. **Colored Output:**
   - If `colorama` is available, log messages are colorized for better readability. Fallbacks to non-colored output if `colorama` is not installed.

---

### Example Usage

```python
# Configure file logging
logger.log_file('logs/application.log')

# Log messages
logger.info("Application started")
logger.debug("Debugging information")
logger.error("An error occurred", stack_info=True)

# Suppress a noisy package logger
logger.suppress_package_logger('noisy_package')

# Stop file logging and release resources
logger.release_log_file()
```