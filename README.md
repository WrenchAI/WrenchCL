<h1 align="center">Wrench Code Library</h1>

<p align="center">
    <img src="https://raw.githubusercontent.com/WrenchAI/WrenchCL/release/resources/img/logo.svg" alt="Logo" style="display: inline-block; vertical-align: middle; margin-bottom: -50px; width: 90%; max-width: 800px;">
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
Upon recieving the below error: 

```bash
ImportError: failed to find libmagic.  Check your installation
```

Install the package with the optional libmagic dependency, users can using the following command:

```bash
1. pip uninstall python-magic -y
2. pip install WrenchCL[libmagic]
```


# User Guides

Sure! Here's an updated and more detailed README that provides extensive instructions on how to use `AWSClientHub`, `RdsServiceGateway`, `S3ServiceGateway`, `ConversationManager`, `OpenAIFactory`, and `OpenAIGateway`. It also includes practical examples for the `Maybe` monad and other utility tools.

### Connecting to AWS Services

To interact with AWS RDS and S3 services, follow these steps:

1. **Setup `AWSClientHub`**:
   ```python
   from WrenchCL.Connections import AwsClientHub

   # Initialize the AWSClientHub using an env file or keyword arguments
   aws_client_hub = AWSClientHub(env_path="path/to/your/env/file")
   # Alternatively, use keyword arguments or existing env variables
   # aws_client_hub = AWSClientHub(aws_profile='your_profile', region_name='your_region', secret_arn='your_secret_arn', ...)
   ```

2. **Using `RdsServiceGateway`**:
   ```python
   from WrenchCL.Connections import RdsServiceGateway

   # Initialize RdsServiceGateway with the AWSClientHub instance
   rds_service = RdsServiceGateway(aws_client_hub)

   # Example: Fetching data from the database
   query = "SELECT * FROM your_table"
   data = rds_service.get_data(query)
   print(data)
   ```

   **Methods in `RdsServiceGateway`**:
   - `get_data(query: str, payload: Optional[dict] = None, fetchall: bool = True, return_dict: bool = True, accepted_type: Optional[Type] = None, none_is_ok: bool = False, accepted_length: Tuple[Optional[int], Optional[int]] = (None, None)) -> Optional[Any]`
     - Fetches data from the database based on the input query and parameters.
   - `update_database(query: str, payload: Union[dict, 'pd.DataFrame'], column_order: Optional[List[str]] = None) -> None`
     - Updates the database by executing the given query with the provided payload.

3. **Using `S3ServiceGateway`**:
   ```python
   from WrenchCL.Connect import S3ServiceGateway

   # Initialize S3ServiceGateway with the AWSClientHub instance
   s3_service = S3ServiceGateway(aws_client_hub)

   # Example: Downloading an object from S3
   bucket_name = "your-bucket-name"
   object_key = "path/to/your/object"
   s3_service.download_object(bucket_name, object_key, "local/path/to/save")
   ```

   **Methods in `S3ServiceGateway`**:
   - `get_object(bucket_name: str, object_key: str) -> io.BytesIO`
     - Retrieves an object from S3.
   - `download_object(bucket_name: str, object_key: str, local_path: str) -> None`
     - Downloads an object from S3 to the local file system.
   - `get_object_headers(bucket_name: str, object_key: str) -> dict`
     - Retrieves the headers of an object in S3.
   - `upload_object(file_path: str, bucket_name: str, object_key: str) -> None`
     - Uploads a local file to S3.
   - `delete_object(bucket_name: str, object_key: str) -> None`
     - Deletes an object from S3.
   - `move_object(src_bucket_name: str, src_object_key: str, dst_bucket_name: str, dst_object_key: str) -> None`
     - Moves an object from one S3 location to another.
   - `copy_object(src_bucket_name: str, src_object_key: str, dst_bucket_name: str, dst_object_key: str) -> None`
     - Copies an object from one S3 location to another.
   - `rename_object(bucket_name: str, src_object_key: str, dst_object_key: str) -> None`
     - Renames an object in S3.
   - `check_object_existence(bucket_name: str, object_key: str) -> bool`
     - Checks if an object exists in S3.
   - `list_objects(bucket_name: str, prefix: Optional[str] = None) -> list`
     - Lists objects in an S3 bucket.
   - `check_bucket_permissions(bucket_name: str) -> dict`
     - Checks the permissions of an S3 bucket.

### Interacting with OpenAI Models

To use OpenAI models, follow these steps:

1. **Setup `OpenAIGateway`**:
   ```python
   from WrenchCL.Models.OpenAI import OpenAIGateway

   # Initialize OpenAIGateway with your OpenAI API key
   openai_gateway = OpenAIGateway(api_key="your_openai_api_key")

   # Example: Generating text
   response = openai_gateway.text_response("Your prompt here")
   print(response)
   ```

   **Methods in `OpenAIGateway`**:
   - `text_response(text: str, model: str = "gpt-3.5-turbo", system_prompt: Optional[str] = None, image_url: Optional[str] = None, json_mode: bool = False,  stream : bool = False, **kwargs) -> Union[str, dict]`
     - Processes text input using the specified model and returns the response.
   - `get_embeddings(text: str, model: str = "text-embedding-3-small") -> list`
     - Retrieves embeddings for the given text using the specified model.
   - `text_to_image(prompt: str, size: str = "1024x1024", quality: str = "standard", n: int = 1) -> str`
     - Generates an image based on the provided prompt.
   - `audio_to_text(audio_path: str, model: str = "whisper-1") -> str`
     - Processes an audio file and returns its transcription.
   - `generate_image_variations(image_path: str, n: int = 1, size: str = "1024x1024") -> str`
     - Creates variations of an image based on the provided image path.
   - `modify_image(image_path: str, prompt: str, mask_path: str, n: int = 1, size: str = "1024x1024") -> str`
     - Edits an image based on the provided prompt and mask.
   - `image_to_text(question: str, image_path: str, **kwargs) -> dict`
     - Processes a vision query based on the provided question and image.
   - `convert_image_to_url_or_base64(image_path: str) -> str`
     - Converts an image to a URL or base64 encoded string.
   - `start_conversation(initial_text: str, **kwargs)`
     - Initiates a conversation using the provided initial text.

2. **Using `OpenAIFactory`**:
   ```python
   from WrenchCL.Models.OpenAI import OpenAIFactory

   # Initialize OpenAIFactory with your OpenAI API key
   openai_factory = OpenAIFactory(api_key="your_openai_api_key")

   # Example: Transcribing audio to text and getting embeddings
   audio_path = "path/to/your/audio/file"
   embeddings = openai_factory.audio_to_text_to_embeddings(audio_path)
   print(embeddings)
   ```

   **Methods in `OpenAIFactory`**:
   - `audio_to_text_to_embeddings(audio_path: str, embedding_model: str = "text-embedding-3-small") -> list`
     - Transcribes audio to text and then generates embeddings for the text.
   - `image_to_text_to_embeddings(image_path: str, question: str, embedding_model: str = "text-embedding-3-small") -> list`
     - Performs a vision query to understand an image and then generates embeddings for the response.
   - `validate_response_with_gpt(initial_response: str, validation_prompt: str) -> str`
     - Uses an initial response and validates or expands upon it with a secondary GPT call.

### Utility Tools

WrenchCL includes several utility tools for various purposes:

Got it! Here is the section about the custom JSON serializer in the specified format:

### Custom JSON Serializer

- **robust_serializer**: Serializes objects not natively serializable by JSON, including `datetime`, `date`, `Decimal`, and custom objects.

    ```python
    # Usage with json_dumps
    from datetime import datetime
    import json
    from WrenchCL.Tools import robust_serializer

    print(json.dumps({"timestamp": datetime.now()}, default=robust_serializer))
    # Output: {"timestamp": "2024-05-17T12:34:56.789012"}
    ```

- **validate_input_dict**: Validates the input dictionary against expected types.
  ```python
  from WrenchCL.Tools import validate_input_dict
    
  params = {
        'event': 'event_data',
        'context': 'context_data',
        'start_time': 1625256000,
        'lambda_client': 'lambda_client_instance'
  }
  expected_types = {
        'event': str,
        'context': str,
        'start_time': (int, float),
        'lambda_client': object,
  }
    
  validate_input_dict(params, expected_types)
  ```

- **Coalesce**: A utility function to return the first non-null value.
  ```python
  from WrenchCL.Tools import coalesce

  result = coalesce(None, "default_value")
  print(result)  # Output: "default_value"
  ```

- **FileTyper**: A utility for determining file types.
  ```python
  from WrenchCL.Tools import get_file_type

  file_type = get_file_type("path/to/your/file")
  print(file_type)
  ```

- **Image2B64**: A utility for encoding images to base64.
  ```python
  from WrenchCL.Tools import image_to_base64

  image_b64 = image_to_base64("path/to/your/image.jpg")
  print(image_b64)
  ```

- **MaybeMonad**: A utility for handling nullable values with method chaining.
  ```python
  from WrenchCL.Tools import Maybe

  maybe_value = Maybe(None).len().end_maybe()
  print(result)  # Output: None
  # Does not raise an exception
  ```

- **WrenchLogger**: A custom logger for advanced logging.
  ```python
  from WrenchCL.Tools import logger

  logger.info("This is an info log message", "with additional info")
  logger.error("This is an error log message", "with error details")
  ```

  **Non-hidden Methods in `WrenchLogger`**:
  
  #### Logging Methods
  - `info(*args: str, stack_info: Optional[bool] = False) -> None`
  - `context(*args: str, stack_info: Optional[bool] = False) -> None`
  - `warning(*args: str, stack_info: Optional[bool] = False) -> None`
  - `HDL_WARN(*args: str, stack_info: Optional[bool] = False) -> None`
  - `error(*args: str, stack_info: Optional[bool] = False) -> None`
  - `data(data: Any, wrap_length: Optional[int] = None, max_rows: Optional[int] = None, stack_info: Optional[bool] = False) -> None`
  - `HDL_ERR(*args: str, stack_info: Optional[bool] = False) -> None`
  - `RECV_ERR(*args: str, stack_info: Optional[bool] = False) -> None`
  - `critical(*args: str, stack_info: Optional[bool] = False) -> None`
  - `debug(*args: str, stack_info: Optional[bool] = False) -> None`
  - `start_time() -> None`
  - `log_time(message: str = "Elapsed time", format: str = "seconds", stack_info: Optional[bool] = False) -> None`
  - `header(text: str, size: int = 80, newline: bool = True) -> None`
  - `compact_header(text: str, size: int = 40) -> None`
  
  **Note**: The logging methods support chaining multiple string arguments.

  #### Configuration Methods
  - `setLevel(level: str) -> None`
    - Changes the reporting level of the logger.
  - `revertLoggingLevel() -> None`
    - Reverts the logging level to the previous level.
  - `set_file_logging(file_logging: bool) -> None`
    - Enables or disables file logging.
  - `set_log_file_location(new_append_mode: Optional[str] = None) -> None`
    - Changes the file append mode and optionally deletes the old file.

  #### Utility Methods
  - `initiate_new_run() -> None`
    - Initiates a new run with a unique run ID.
  - `overwrite_lambda_mode(setting: bool) -> None`
    - Sets whether the logger is running on AWS Lambda.
  - `set_global_traceback(setting: bool) -> None`
    - Sets whether to always include stack traces for errors.
  - `release_resources() -> None`
    - Releases file handler resources.

  ```python
  # Example usage of logger methods
  logger.info("This is an info log message", "with additional info")
  logger.context("This is a contextual log message", "with more context")
  logger.warning("This is a warning log message")
  logger.HDL_WARN("This is a handled warning log message")
  logger.error("This is an error log message", str(Exception("Example exception")), stack_info=True)
  
  data_dict = {"key": "value", "another_key": 123}
  logger.data(data_dict, wrap_length=40, max_rows=10)

  logger.HDL_ERR("This is a handled error log message")
  logger.RECV_ERR("This is a recoverable error log message", "with additional recoverable error details")
  logger.critical("This is a critical log message", "with critical details", stack_info=True)
  logger.debug("This is a debug log message", str(data_dict), stack_info=True)
  
  logger.start_time()
  # ... some operations ...
  logger.log_time("Processing time", format="formatted")
  
  logger.initiate_new_run()
  logger.overwrite_lambda_mode(setting=True)
  logger.set_global_traceback(setting=True)
  logger.setLevel("DEBUG")
  
  logger.header("Header Text")
  logger.compact_header("Compact Header Text")
  ```
  
- **FetchMetaData**: A utility to retrieve metadata from a URL or local file path.
  ```python
  from WrenchCL.Tools import get_metadata

  # Get metadata from a URL
  url_metadata = get_metadata("https://example.com/file.txt")
  print(url_metadata)
  # Output: {'content_type': 'text/plain', 'content_length': '1234', 'last_modified': datetime.datetime(2023, 5, 17, 12, 34, 56), 'url': 'https://example.com/file.txt'}

  # Get metadata from a local file
  file_metadata = get_metadata("/path/to/file.txt", is_url=False)
  print(file_metadata)
  # Output: {'file_path': '/path/to/file.txt', 'file_size': 1234, 'creation_time': '2023-05-17T12:34:56', 'mime_type': 'text/plain'}
  ```
  
### Decorators

WrenchCL includes several decorators for common patterns:

- **Retryable**: Retries a function call if specified exceptions occur.
  ```python
  from WrenchCL.Decorators import Retryable

  @Retryable(retry_on_exceptions=(ValueError,), max_retries=3, delay=2)
  def might_fail():
      if random.random() < 0.5:
          raise ValueError("Random failure")
      return "Success"

  result = might_fail()
  print(result)
  ```

- **SingletonClass**: Ensures a class only has one instance.
  ```python
  from WrenchCL.Decorators import SingletonClass

  @SingletonClass
  class MySingleton:
      def __init__(self):
          self.value = 42

  instance1 = MySingleton()
  instance2 = MySingleton()
  print(instance1 is instance2)  # Output: True
  ```

- **TimedMethod**: Logs the time taken to execute a method.
  ```python
  from WrenchCL.Decorators import TimedMethod

  @TimedMethod
  def slow_function():
      time.sleep(2)
      return "Done"

  result = slow_function()
  print(result)  # Output: "Done"
  ```

### DataFlow

WrenchCL includes various helper functions to assist with common tasks. These helpers are located in the `DataFlow` module.

#### build_return_json

Constructs a JSON response with a given status code and message.

```python
from WrenchCL.DataFlow import build_return_json

response = build_return_json(code=200, message="Success")
print(response)  # Output: {'statusCode': 200, 'body': '{"message": "Success"}'}
```

#### handle_lambda_response

Handles Lambda function responses, including logging and error handling. It stops the Lambda function execution and returns a specified response when a `GuardedResponseTrigger` exception is raised. This is particularly useful for ensuring that the Lambda function exits immediately and returns the correct response, even if the exception occurs deep within nested function calls.

Here’s a comprehensive example demonstrating how to use `handle_lambda_response` and `GuardedResponseTrigger` to handle errors and propagate responses up the call hierarchy in an AWS Lambda function.

```python
import time
from WrenchCL import wrench_logger
from WrenchCL.DataFlow import build_return_json, handle_lambda_response, GuardedResponseTrigger


# Mock implementation of LambdaCore for the example
class LambdaCore:
    def __init__(self, event, context):
        self.event = event
        self.context = context

    def route(self):
        # Example of nested function call where an error might occur
        self.process_request()

    def process_request(self):
        try:
            # Perform some processing
            self.get_score({"key": "value"}, {"input_key": "input_value"})
        except Exception as e:
            # Handle other exceptions and wrap them into the GuardedResponseTrigger
            handle_lambda_response(500, str(e),
                                   {"event": self.event, "context": self.context, "start_time": time.time(),
                                    "lambda_client": "lambda_client_instance"})

    def get_score(self, target_dict, input_dict):
        # Mock scoring process which might throw an error
        try:
            score = self.compute_score(target_dict, input_dict)
            if score is None:
                handle_lambda_response(732, "Prediction Error: Invalid prediction provided by model.",
                                       {"event": self.event, "context": self.context, "start_time": time.time(),
                                        "lambda_client": "lambda_client_instance"})
            handle_lambda_response(200, f"Score computed successfully: {score}",
                                   {"event": self.event, "context": self.context, "start_time": time.time(),
                                    "lambda_client": "lambda_client_instance"})
        except GuardedResponseTrigger as e:
            raise e  # Propagate the GuardedResponseTrigger upwards
        except Exception as e:
            handle_lambda_response(757, str(e),
                                   {"event": self.event, "context": self.context, "start_time": time.time(),
                                    "lambda_client": "lambda_client_instance"})

    def compute_score(self, target_dict, input_dict):
        # This is a placeholder for the actual scoring logic
        # Raise an error to simulate a failure
        raise ValueError("Simulated scoring error")


def lambda_handler(event, context):
    wrench_logger.initiate_new_run()

    if event.get('is_warmer'):
        wrench_logger.run_id = 'R-LAMBDAS-WARM'
        wrench_logger.context("Lambda Warmed")
        return build_return_json(200, 'Warmed Lambda')

    start_time = time.time()
    try:
        wrench_logger.info("Invoking Lambda Core")
        lambda_core_instance = LambdaCore(event=event, context=context)
        lambda_core_instance.route()
        wrench_logger.info(f"Finished Run in {round(time.time() - start_time, 2)} seconds")
    except GuardedResponseTrigger as e:
        wrench_logger.info(f"Finished Run in {round(time.time() - start_time, 2)} seconds")
        return e.get_response()
    except Exception as e:
        wrench_logger.error(e, stack_info=True)
        return build_return_json(500, str(e))
```

**Explanation:**

1. **Lambda Handler**: The entry point of the Lambda function. It initiates a new run for the logger and checks if the Lambda is being warmed up. It then attempts to create an instance of `LambdaCore` and routes the event to it.

2. **LambdaCore**: This class processes the Lambda event. It contains nested function calls:
   - `route()`: Routes the event to `process_request()`.
   - `process_request()`: Calls `get_score()`.
   - `get_score()`: Calls `compute_score()`, and uses `handle_lambda_response` to handle any errors.

3. **Error Handling**: 
   - If `compute_score()` raises an error, it is caught in `get_score()`.
   - `handle_lambda_response()` is called with an appropriate status code and message.
   - If a `GuardedResponseTrigger` is raised, it is propagated up to `lambda_handler`.

4. **GuardedResponseTrigger**: This custom exception ensures that when an error is encountered deep in the call hierarchy, the Lambda function stops execution and returns a response immediately. This response is propagated back up through the nested calls to the top-level Lambda handler.

By using `GuardedResponseTrigger` and `handle_lambda_response`, you can manage errors effectively and ensure that your Lambda function returns the correct response even when an error occurs deep within nested function calls.

#### trigger_minimum_dataflow_metrics

Triggers minimal data flow metrics for monitoring purposes.

```python
from WrenchCL.DataFlow import trigger_minimum_dataflow_metrics

trigger_minimum_dataflow_metrics(event="event_data", context="context_data", start_time=1625256000,
    lambda_client="lambda_client_instance", job_name="Model Inference Service", job_type="Lambda", status_code="200",
    message="Success")
```

#### trigger_dataflow_metrics

Triggers detailed data flow metrics for monitoring purposes.

```python
from WrenchCL.DataFlow import trigger_dataflow_metrics

trigger_dataflow_metrics(event="event_data", context="context_data", start_time=1625256000,
    lambda_client="lambda_client_instance", job_name="Model Inference Service", job_type="Lambda", status_code="200",
    message="Success", additional_data={"key": "value"})
```

With these detailed instructions and examples, you should be well-equipped to utilize the WrenchCL library for your projects. If you have any further questions or need additional support, please refer to the documentation or contact the maintainers.
