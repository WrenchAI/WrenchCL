<h1 align="center">Wrench Code Library</h1>

<p align="center">
    <a href="https://pypi.org/project/WrenchCL/" style="text-decoration: none;">
        <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/WrenchCL?logo=pypi&logoColor=green&color=green">
    </a>
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/WrenchCL?logo=python&logoColor=blue&color=yellow">
    <a href="https://github.com/Kydoimos97" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/Kydoimos97-cb632b?label=Code%20Maintainer" alt="Maintainer" height="20"/>
    </a>    
    <br> <br>
    <a href="https://github.com/WrenchAI/WrenchCL/actions/workflows/publish-to-pypi.yml" style="text-decoration: none;">
        <img alt="GitHub Workflow Status (with event)" src="https://img.shields.io/github/actions/workflow/status/WrenchAI/WrenchCL/publish-to-pypi.yml?event=push&logo=Github&label=Test%20%26%20Publish%20%F0%9F%90%8D%20to%20PyPI%20%F0%9F%93%A6">
    </a>
</p>

## Description

This is a code library designed to improve code reusability and standardize access to APIs, RDS, and logging functionalities.

**PyPI Link:** [WrenchCL on PyPI](https://pypi.org/project/WrenchCL/)

## Installation

To install the package, simply run the following command:

```bash
pip install WrenchCL
```

# User Guides

# Wrench Logger

## Instantiation

WrenchCL can be imported using either of the following methods:

```python
from WrenchCL import wrench_logger
# or
from WrenchCL.Utility import wrench_logger
```

It utilizes a singleton instance. Upon import, the `wrench_logger` automatically:

1. Generates a run ID.
2. Checks the environment it's running on and sets the configuration accordingly.
3. Sets the default logging format.
4. Sets the logging level as specified.
5. Configures the file logger if file logging is enabled.
6. Configures the console logger.

Since the class itself is not imported but the instance is, configuration is achieved through methods rather than arguments.

## Logging Format Details

Each log message encompasses the following information:

- **Log Level:** Severity of the log (e.g., INFO, DEBUG).
- **Run ID:** Unique identifier for the current run, aiding in distinguishing logs from different execution phases.
- **File Name:** The Python file where the log call occurs.
- **Function Name:** Function containing the log call.
- **Line Number:** Exact line number of the log call.
- **Timestamp:** Date and time when the log message was generated.
- **Message:** Content of the log message.

#### Format 

```[Log Level]  :  [RunID] FileName:Method:Lineno  | DateTime | Message```

```INFO    :  [R-2P19UD-6573] WrenchLogger.py:_log:156  | 2024-02-21 01:30:11 | RDS: Getting Entity Data```

## Main Functional Methods

<details>
  <summary><span style="font-size: large;">Logging Methods</span></summary>

---

#### `info` Method

```python
wrench_logger.info(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.info("Test info message.")
  # Output 
  INFO    :  [R-HH7GH3-9471] WrenchLogger.py:info:192  | 2024-02-22 12:15:04 | Test info message.
  ```

- **Color:** Green
- **Use Case:** For printing information.

---

#### `context` Method

```python
wrench_logger.context(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
    # Input
  wrench_logger.context("Test context message.")
  # Output 
  INFO    :  [R-HH7GH3-9471] WrenchLogger.py:context:195  | 2024-02-22 12:15:04 | Test context message.
  ```

- **Color:** Purple
- **Use Case:** For printing large volumes of context, making it easily distinguishable during testing.

---

#### `warning` Method

```python
wrench_logger.warning(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.warning("Test warning message.")
  # Output 
  WARNING :  [R-HH7GH3-9471] WrenchLogger.py:warning:198  | 2024-02-22 12:15:04 | Test warning message.
  ```

- **Color:** Yellow
- **Use Case:** For a handled exception.

---

#### `error` Method

```python
wrench_logger.error(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.error("Test error message.")
  # Output 
  ERROR   :  [R-HH7GH3-9471] WrenchLogger.py:error:201  | 2024-02-22 12:15:04 | Test error message.
  ```

- **Color:** Red
- **Use Case:** For handled or unhandled errors.

---

#### `critical` Method

```python
wrench_logger.critical(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.critical("Test critical message.")
  # Output 
  CRITICAL:  [R-HH7GH3-9471] WrenchLogger.py:critical:204  | 2024-02-22 12:15:04 | Test critical message.
  ```

- **Color:** Light-red
- **Use Case:** For high priority errors that significantly impact outputs or dependencies.

---

#### `debug` Method

```python
wrench_logger.debug(self, text: str, stack_info: Optional[bool] = False) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.debug("Test debug message.")
  # Output 
  DEBUG   :  [R-HH7GH3-1289] WrenchLogger.py:debug:207  | 2024-02-22 12:30:48 | Test debug message.
  ```

- **Color:** Light-blue
- **Use Case:** For debugging information.

---

#### `header` Method

```python
wrench_logger.header(self, text: str, size: int = 80, newline: bool = True) -> None
```

- **Usage:**

  ```python
  # Input
  wrench_logger.header("Test Header")
  # Output 

    ----------------------------------Test Header-----------------------------------
  ```

- **Use Case:** To create sections in logs. 
- `newline` adds a white line above the header. 
- `size` determines the string's total length, filled with `-`.

</details>

---

## Configuration Methods

<details>
  <summary><span style="font-size: large;">Level and Configuration methods</span></summary>

---

### Set Level

```python
wrench_logger.setLevel(self, level: str) -> None
```

- **Purpose:** Adjusts the logging level to control what severity of logs are emitted. 
- Valid levels include ```"INFO", "DEBUG", "WARNING", "ERROR", and "CRITICAL".```


**Example:**

  ```python
  wrench_logger.setLevel("DEBUG")
  ```

This sets the logging level to DEBUG, ensuring that all debug messages and above are logged.

---

### Revert Logging Level

```python
wrench_logger.revertLoggingLevel(self) -> None
```

- **Purpose:** Reverts the logging level to the previous setting. Useful for temporary adjustments of log verbosity.

**Example:**

  ```python
    # Initial Setting
    wrench_logger.setLevel("DEBUG")
    # -- non verbose code
    wrench_logger.setLevel("INFO") # Switch to Info level
    # -- verbose_function
    wrench_logger.revertLoggingLevel() # Switch back to last level before info; debug
  ```

---

### Overwrite lambda mode

```python
wrench_logger.overwrite_lambda_mode(self, setting: bool) -> None
```

- **Purpose:** Overrides the default behavior for color logging in environments like AWS Lambda, where color logging might not be supported.

**Example:**

  ```python
  wrench_logger.overwrite_lambda_mode(False)
  ```

---

### Set Global Traceback

```python
wrench_logger.set_global_traceback(self, setting: bool) -> None
```

- **Purpose:** Globally enables or disables the inclusion of traceback information in logs, aiding in debugging without having to enable it per log call.

**Example:**

  ```python
  wrench_logger.set_global_traceback(True)
  ```

Enabling this will append traceback information to all log messages
</details>

---

<details>
  <summary><span style="font-size: large;">File Logging Methods</span></summary>

---

### Set log file location

```python
wrench_logger.set_log_file_location(self, path: str, new_append_mode: Optional[str] = None) -> None
```

- **Purpose:** Specifies the log file's location and the mode of appending to the log file. This is crucial for managing log file output and retention.

**Example:**

  ```python
  wrench_logger.set_log_file_location("/var/log/my_app.log")
  ```

Sets the log file location to `/var/log/my_app.log`, directing all file-based logging output to this file.

---

### Set file logging

```python
wrench_logger.set_file_logging(self, file_logging: bool) -> None
```

- **Purpose:** Enables or disables logging to a file. This method provides a straightforward way to toggle file logging according to runtime decisions.

**Example:**

  ```python
  wrench_logger.set_file_logging(True)
  ```

This enables logging to a file, ensuring that logs are not only displayed in the console but also saved for later review.

---

### Release Resources

```python
wrench_logger.release_resources(self) -> None
```

- **Purpose:** Ensures that all file handles and other resources are properly closed and released. This is particularly important in long-running applications to avoid resource leaks.

**Example:**

  ```python
  wrench_logger.release_resources()
  ```

Calling this method when the application is shutting down or when logging needs to be reconfigured ensures that resources are cleanly released.

</details>
