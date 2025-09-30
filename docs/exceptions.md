# Exceptions

WrenchCL provides a structured exception hierarchy with intelligent error suggestions and clear error messages.

## Import Structure

```python
from WrenchCL.Exceptions import (
    InvalidConfigurationException, InitializationException,
    ArgumentTypeException, ValidationTypeException,
    ReferenceNotFoundException, SecurityViolationException
    )
```

## Initialization Exceptions

### InvalidConfigurationException

For configuration errors:

```python
from WrenchCL.Exceptions import InvalidConfigurationException

# Basic usage
raise InvalidConfigurationException("Database connection failed")

# With detailed context
raise InvalidConfigurationException(
        config_name="AWS_RDS_CONFIG",
        reason="Missing SECRET_ARN environment variable"
        )


# In configuration classes
class DatabaseConfig:
    def __init__(self, config_dict):
        if 'host' not in config_dict:
            raise InvalidConfigurationException(
                    config_name="DatabaseConfig",
                    reason="Missing required 'host' parameter"
                    )
```

### IncompleteInitializationException

When objects are used before proper initialization:

```python
from WrenchCL.Exceptions import IncompleteInitializationException


class DatabaseManager:
    def __init__(self):
        self._initialized = False

    def initialize(self, connection_string):
        self._connection = create_connection(connection_string)
        self._initialized = True

    def execute_query(self, query):
        if not self._initialized:
            raise IncompleteInitializationException(
                    "DatabaseManager must be initialized before use"
                    )
        return self._connection.execute(query)
```

### InitializationException

When initialization fails:

```python
from WrenchCL.Exceptions import InitializationException


class ServiceManager:
    def __init__(self, config):
        try:
            self.api_client = create_api_client(config['api_key'])
            self.database = connect_to_database(config['db_url'])
        except Exception as e:
            raise InitializationException(
                    f"Failed to initialize ServiceManager: {e}"
                    ) from e
```

## Argument and Validation Exceptions

### ArgumentTypeException

For type validation errors:

```python
from WrenchCL.Exceptions import ArgumentTypeException


def process_data(data, batch_size=100):
    if not isinstance(data, (list, tuple)):
        raise ArgumentTypeException(
                f"Expected list or tuple for data, got {type(data).__name__}"
                )

    if not isinstance(batch_size, int):
        raise ArgumentTypeException(
                f"batch_size must be an integer, got {type(batch_size).__name__}"
                )
```

### ArgumentValueException

For value validation errors:

```python
from WrenchCL.Exceptions import ArgumentValueException


def set_retry_count(count):
    if count < 0:
        raise ArgumentValueException("Retry count cannot be negative")

    if count > 100:
        raise ArgumentValueException("Retry count cannot exceed 100")


def calculate_percentage(value, total):
    if total == 0:
        raise ArgumentValueException("Total cannot be zero")
```

### ValidationTypeException

For structured validation with field details:

```python
from WrenchCL.Exceptions import ValidationTypeException


def validate_user_data(user_data):
    required_fields = {'username': str, 'email': str, 'age': int}

    for field, expected_type in required_fields.items():
        if field not in user_data:
            raise ValidationTypeException(
                    field=field,
                    expected="required field",
                    actual="missing"
                    )

        value = user_data[field]
        if not isinstance(value, expected_type):
            raise ValidationTypeException(
                    field=field,
                    expected=expected_type.__name__,
                    actual=type(value).__name__
                    )
```

### InvalidPayloadException

For payload validation with missing fields tracking:

```python
from WrenchCL.Exceptions import InvalidPayloadException


def process_api_request(payload):
    required_fields = ['user_id', 'action', 'timestamp']
    missing_fields = [f for f in required_fields if f not in payload]

    if missing_fields:
        raise InvalidPayloadException(
                missing_fields=missing_fields,
                message=f"Missing required fields: {', '.join(missing_fields)}"
                )
```

## Miscellaneous Exceptions

### ReferenceNotFoundException

For missing references or resources:

```python
from WrenchCL.Exceptions import ReferenceNotFoundException


class ConfigRegistry:
    def __init__(self):
        self._configs = {}

    def get_config(self, name):
        if name not in self._configs:
            available = list(self._configs.keys())
            raise ReferenceNotFoundException(
                    variable_name=name,
                    message=f"Configuration '{name}' not found. Available: {available}"
                    )
        return self._configs[name]


def get_user_by_id(user_id):
    user = database.query("SELECT * FROM users WHERE id = %s", (user_id,))
    if not user:
        raise ReferenceNotFoundException(
                variable_name=f"user_id={user_id}",
                message=f"User with ID {user_id} does not exist"
                )
    return user
```

### SecurityViolationException

For security-related errors:

```python
from WrenchCL.Exceptions import SecurityViolationException


def validate_file_upload(filename, content):
    dangerous_extensions = ['.exe', '.bat', '.sh']
    if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
        raise SecurityViolationException(f"File type not allowed: {filename}")

    if b'<script>' in content.lower():
        raise SecurityViolationException("File contains malicious content")


def authenticate_user(token):
    if not token:
        raise SecurityViolationException("Authentication token required")

    if len(token) < 32:
        raise SecurityViolationException("Invalid token format")
```

### GuardedResponseTrigger

For Lambda function early returns:

```python
from WrenchCL.Exceptions import GuardedResponseTrigger
import json


def lambda_handler(event, context):
    try:
        result = process_request(event)
        return {'statusCode': 200, 'body': json.dumps(result)}

    except ValidationError as e:
        response = {
                'statusCode': 400,
                'body': json.dumps({'error': 'Validation failed'})
                }
        raise GuardedResponseTrigger(response)


# Lambda wrapper
def handle_lambda_errors(handler_func):
    def wrapper(event, context):
        try:
            return handler_func(event, context)
        except GuardedResponseTrigger as e:
            return e.get_response()
        except Exception:
            return {'statusCode': 500, 'body': '{"error": "Internal error"}'}

    return wrapper
```

## Exception Suggestions

WrenchCL includes an intelligent suggestion system for attribute errors:

```python
class User:
    def __init__(self):
        self.username = "john"
        self.email = "john@example.com"


user = User()
try:
    print(user.usernme)  # Typo
except AttributeError as e:
    # When logged with WrenchCL logger, includes suggestion:
    # "Did you mean: username?"
    from WrenchCL import logger

    logger.error("Attribute error", exc_info=True)
```

## Exception Chaining

Use exception chaining for better error context:

```python
def load_config():
    try:
        config = json.load(open('config.json'))
        validate_config(config)
        return config
    except FileNotFoundError as e:
        raise InvalidConfigurationException(
                config_name="database",
                reason="Configuration file not found"
                ) from e
    except json.JSONDecodeError as e:
        raise InvalidConfigurationException(
                config_name="database",
                reason="Invalid JSON format"
                ) from e


def initialize_service():
    try:
        config = load_config()
        return create_service(config)
    except InvalidConfigurationException as e:
        raise InitializationException(
                "Service initialization failed"
                ) from e
```

## Best Practices

### Specific Error Messages

```python
# Good: Specific and actionable
raise ArgumentValueException("Port must be between 1 and 65535, got 70000")

# Avoid: Vague error messages
raise ArgumentValueException("Invalid port")
```

### Exception Context

```python
# Add context to help debugging
try:
    process_batch(data)
except Exception as e:
    raise ValidationTypeException(
            field="batch_data",
            expected="valid format",
            actual="corrupted",
            message=f"Batch processing failed at record {current_record}: {e}"
            ) from e
```

### Graceful Degradation

```python
def get_data_with_fallback(source):
    try:
        return primary_source.get_data(source)
    except ReferenceNotFoundException:
        logger.warning(f"Primary source unavailable for {source}, using fallback")
        return fallback_source.get_data(source)
```

All exceptions integrate with WrenchCL's logging system to provide detailed error information and suggestions when available.