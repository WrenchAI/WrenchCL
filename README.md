<h1 align="center">Wrench Code Library</h1>

<p align="center">
  <br>
  <a href="https://pypi.org/project/WrenchCL/"><img src="https://badge.fury.io/py/WrenchCL.svg" alt="PyPI version" height="20"/></a>
  <img src="https://img.shields.io/badge/python-3.x-blue" alt="Python Version" height="20"/>
  <a href="https://github.com/Kydoimos97"><img src="https://img.shields.io/badge/maintainer-Kydoimos97-yellow" alt="Maintainer" height="20"/></a>
  <br><br>
  <a href="https://github.com/WrenchAI/WrenchCL/stargazers"><img src="https://img.shields.io/github/stars/WrenchAI/WrenchCL.svg" alt="GitHub Stars" height="20"/></a>
  <a href="https://github.com/WrenchAI/WrenchCL/network/members"><img src="https://img.shields.io/github/forks/WrenchAI/WrenchCL.svg" alt="GitHub Forks" height="20"/></a>
  <a href="https://github.com/WrenchAI/WrenchCL/issues"><img src="https://img.shields.io/github/issues/WrenchAI/WrenchCL.svg" alt="GitHub Issues" height="20"/></a>
  <a href="https://github.com/WrenchAI/WrenchCL/pulls"><img src="https://img.shields.io/github/issues-pr/WrenchAI/WrenchCL.svg" alt="GitHub Pull Requests" height="20"/></a>

  
</p>

## Description

This is a code library designed to improve code reusability and standardize access to APIs, RDS, and logging functionalities.

**Pypi Link: [https://pypi.org/project/WrenchCL/](https://pypi.org/project/WrenchCL/)**

## Installation

To install the package, simply run:

```bash
pip install WrenchCL
```

## Usage

---

### ApiSuperClass:
The `ApiSuperClass` is part of the `WrenchCL` module and serves as a skeleton for creating API interaction classes. The class handles the details of API calls, data batching, logging, and error handling. It is intended to be subclassed, with `get_count` and `fetch_data` methods to be implemented in the subclass.

#### Create a Subclass to Implement the Abstract Methods
`ApiSuperClass` is designed to be subclassed. You'll need to implement the `get_count` and `fetch_data` methods in your subclass.

Example:
```python
class MyApiClass(ApiSuperClass):
    def get_count(self):
        # Implement code to get the total count of records/pages.
        return 1000
    
    def fetch_data(self, batch_size, last_record_sort_value=None, last_record_unique_id=None, page=None):
        # Implement code to fetch data
        return [], last_record_sort_value, last_record_unique_id, False  # Example placeholders
```

#### Initialize Your Subclass
Create an instance of your subclass and initialize it with the base URL of the API.

```python
api_instance = MyApiClass("https://api.example.com")
```

#### Use the `batch_processor` Method
Call the `batch_processor` method to fetch data in batches.

```python
data = api_instance.batch_processor(batch_size=100, max_retries=5)
```

This will return a Pandas DataFrame containing all the fetched data.

#### Logging and Error Handling
The class uses a custom logging package (`wrench_logger`) which is part of the WrenchCL module. Make sure the logger is configured appropriately in your environment.

#### Data Types and Structures:

- `get_count` should return an integer for the total record or page count.
- `fetch_data` should return a tuple containing: a batch of records, the last record's sort value, the last record's unique ID, and a boolean flag for more records.

#### Warnings:

- Properly implement `get_count` and `fetch_data` in your subclass to avoid NotImplementedError.
- If you exceed the maximum number of retries, a `MaxRetriesExceededError` will be raised.

---

### ChatGptSuperClass:
The `ChatGptSuperClass` is designed to serve as a base class for interacting with the ChatGPT API. The class handles API requests, response parsing, logging, and retries using the `tenacity` library. You are expected to subclass it and implement methods like `_message_generator` and `_function_generator`.

#### Create a Subclass to Implement the Abstract Methods
You'll need to implement the `_message_generator` and `_function_generator` methods in your subclass.

Example:
```python
class MyChatGptClass(ChatGptSuperClass):
    def _message_generator(self):
        # Implement the message generation logic here.
        self.message = [...]  # A list of messages, presumably.
    
    def _function_generator(self):
        # Implement the function generation logic here, or pass None if not needed.
        self.function = ...  # Your function logic here.
```

#### Initialize Your Subclass
Create an instance of your subclass. Optionally, you can provide the path to a `.env` file containing the secrets required for API interaction.

```python
chat_instance = MyChatGptClass(secrets_path='../resources/secrets/MySecrets.env')
```

#### Access the Response
After initialization, the `fetch_response` method is automatically called. You can access the parsed response using `chat_instance.response`.

#### Logging and Error Handling
The class uses the `wrench_logger` for logging, make sure it's configured appropriately in your environment.

#### Data Types and Structures:

- `self.message`: Should be a list containing the chat messages.
- `self.function`: Variable type could vary based on what you're doing but generally, could be a callable or any object that defines custom functionality.

#### Warnings:

- `_message_generator` and `_function_generator` should be implemented in your subclass to avoid a NotImplementedError.

#### Object-Oriented Principles:
The design of the class adheres to the SOLID principles. Specifically, it follows the Open/Closed principle as it is open for extension but closed for modification. Additionally, the use of abstract methods suggests adherence to the Liskov Substitution Principle.

#### AWS, Retry and Other Notes:
- If you're deploying this in an AWS environment, make sure your secrets and environment variables are securely managed, possibly using AWS Secrets Manager.
- The class uses exponential backoff for retries, configurable via the `tenacity` library.

---

### _RdsSuperClass
The `_RdsSuperClass` is designed for seamless interaction with a PostgreSQL database. It can connect, execute queries, and parse the results to either JSON or a DataFrame. Below are the detailed instructions on how to use this class.

#### Connect to the Database

Before executing any queries, establish a connection to the database. Ensure your `.env` file containing database secrets is accessible.

```python
rdsInstance.connect()
```

#### Execute a Query

Use the `execute_query` method to run SQL queries. The method takes up to three parameters:
- `query`: SQL query as a string. (Required)
- `output`: Desired output format, either `'json'` or `'dataframe'`. (Optional)
- `method`: Fetching method, either `'fetchall'` or `'fetchone'`. (Optional, default is `'fetchall'`)

Here is how you would execute a SQL SELECT query:

```python
result = rdsInstance.execute_query("SELECT * FROM table_name", output='json', method='fetchall')
```

#### Parse Results

If you want the result to be automatically parsed to JSON or DataFrame, you can specify the `output` parameter in `execute_query` as shown in step 3.

Alternatively, you can manually call the parsing methods:

- To parse the result to JSON:

```python
json_result = rdsInstance.parse_to_json()
```

- To parse the result to a DataFrame:

```python
df_result = rdsInstance.parse_to_dataframe()
```

#### Close the Connection

After all database operations, it's a good practice to close the connection:

```python
rdsInstance.close()
```

#### Example Usage

Putting it all together, here's a sample code snippet:

```python
from WrenchCL import rdsInstance

# Step 2
rdsInstance.connect()

# Step 3
result_as_json = rdsInstance.execute_query("SELECT * FROM users", output='json', method='fetchall')

# Optional: Manual Parsing in Step 4
# json_result = rdsInstance.parse_to_json()

# Step 5
rdsInstance.close()
```

---

### Wrench_Logger

#### Importing the Logger

1. Import the instantiated logger object:
    ```python
    from your_module import wrench_logger
    ```

#### Logging Messages

- **Info Message**
    ```python
    wrench_logger.info("This is an info message.")
    ```

- **Warning Message**
    ```python
    wrench_logger.warning("This is a warning message.")
    ```

- **Error Message**
    ```python
    wrench_logger.error("This is an error message.")
    ```

- **Critical Message**
    ```python
    wrench_logger.critical("This is a critical message.")
    ```

- **Debug Message**
    ```python
    wrench_logger.debug("This is a debug message.")
    ```

#### Log Exceptions and Tracebacks
- **Log Traceback**
    ```python
    try:
        # some code that raises an exception
    except Exception as e:
        wrench_logger.log_traceback(e)
    ```

#### Additional Formatting

- **Header Message**
    ```python
    wrench_logger.header("Your Header Text", size=80)
    ```

#### Release Resources
- **Release File Handler Resources**
    ```python
    wrench_logger.release_resources()
    ```

---
