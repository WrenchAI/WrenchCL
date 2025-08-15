# Exception Handling

WrenchCL provides a comprehensive exception hierarchy with intelligent error suggestions, structured error messages, and specialized exceptions for different error categories. The exception system is designed to provide clear, actionable error information to help developers quickly identify and resolve issues.

## Exception Hierarchy

The WrenchCL exception system is organized into logical categories:

- **Initialization Exceptions** - Configuration and setup errors
- **Argument Exceptions** - Parameter validation and type errors
- **Miscellaneous Exceptions** - Security, reference, and Lambda-specific errors

## Initialization Exceptions

### InvalidConfigurationException

::: WrenchCL.Exceptions.InvalidConfigurationException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import InvalidConfigurationException

# Basic usage
raise InvalidConfigurationException("Database connection failed")

# With detailed context
raise InvalidConfigurationException(
    config_name="AWS_RDS_CONFIG",
    reason="Missing SECRET_ARN environment variable"
)

# Usage in configuration classes
class DatabaseConfig:
    def __init__(self, config_dict):
        if 'host' not in config_dict:
            raise InvalidConfigurationException(
                config_name="DatabaseConfig",
                reason="Missing required 'host' parameter"
            )
        
        if not config_dict.get('port'):
            raise InvalidConfigurationException(
                config_name="DatabaseConfig",
                reason="Port must be specified and non-zero"
            )
```

### IncompleteInitializationException

::: WrenchCL.Exceptions.IncompleteInitializationException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import IncompleteInitializationException

class DatabaseManager:
    def __init__(self):
        self._initialized = False
        self._connection = None
    
    def initialize(self, connection_string):
        self._connection = create_connection(connection_string)
        self._initialized = True
    
    def execute_query(self, query):
        if not self._initialized:
            raise IncompleteInitializationException(
                "DatabaseManager must be initialized before use. Call initialize() first."
            )
        return self._connection.execute(query)

# Usage
db = DatabaseManager()
try:
    db.execute_query("SELECT * FROM users")  # Raises exception
except IncompleteInitializationException as e:
    print(f"Error: {e}")
    db.initialize("postgresql://...")
    db.execute_query("SELECT * FROM users")  # Now works
```

### InitializationException

::: WrenchCL.Exceptions.InitializationException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import InitializationException

class ServiceManager:
    def __init__(self, config):
        try:
            self.api_client = create_api_client(config['api_key'])
            self.database = connect_to_database(config['db_url'])
            self.cache = setup_cache(config['redis_url'])
        except Exception as e:
            raise InitializationException(
                f"Failed to initialize ServiceManager: {e}"
            ) from e

# Usage with proper error handling
try:
    service = ServiceManager(config)
except InitializationException as e:
    logger.error("Service initialization failed", exc_info=True)
    # Handle graceful degradation or exit
    sys.exit(1)
```

## Argument and Validation Exceptions

### ArgumentTypeException

::: WrenchCL.Exceptions.ArgumentTypeException
    options:
      show_source: false
      heading_level: 4

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
    
    if batch_size <= 0:
        raise ArgumentValueException("batch_size must be positive")

# Type validation decorator
def validate_types(**type_specs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            for param_name, expected_type in type_specs.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise ArgumentTypeException(
                            f"Parameter '{param_name}' must be {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator

@validate_types(data=list, threshold=float)
def analyze_data(data, threshold=0.5):
    return [x for x in data if x > threshold]
```

### ArgumentValueException

::: WrenchCL.Exceptions.ArgumentValueException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import ArgumentValueException

def set_retry_count(count):
    if count < 0:
        raise ArgumentValueException("Retry count cannot be negative")
    
    if count > 100:
        raise ArgumentValueException("Retry count cannot exceed 100")
    
    self.retry_count = count

def calculate_percentage(value, total):
    if total == 0:
        raise ArgumentValueException("Total cannot be zero (division by zero)")
    
    if value < 0 or total < 0:
        raise ArgumentValueException("Values must be non-negative")
    
    return (value / total) * 100

# Range validation utility
def validate_range(value, min_val=None, max_val=None, param_name="value"):
    if min_val is not None and value < min_val:
        raise ArgumentValueException(
            f"{param_name} must be >= {min_val}, got {value}"
        )
    
    if max_val is not None and value > max_val:
        raise ArgumentValueException(
            f"{param_name} must be <= {max_val}, got {value}"
        )

# Usage
def configure_batch_size(size):
    validate_range(size, min_val=1, max_val=10000, param_name="batch_size")
    self.batch_size = size
```

### ValidationTypeException

::: WrenchCL.Exceptions.ValidationTypeException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import ValidationTypeException

class UserValidator:
    def validate_user_data(self, user_data):
        required_fields = {
            'username': str,
            'email': str,
            'age': int,
            'active': bool
        }
        
        for field, expected_type in required_fields.items():
            if field not in user_data:
                raise ValidationTypeException(
                    field=field,
                    expected=f"required field",
                    actual="missing"
                )
            
            value = user_data[field]
            if not isinstance(value, expected_type):
                raise ValidationTypeException(
                    field=field,
                    expected=expected_type.__name__,
                    actual=type(value).__name__
                )
        
        # Additional validation
        if '@' not in user_data['email']:
            raise ValidationTypeException(
                field='email',
                expected='valid email format',
                actual=user_data['email']
            )

# Schema validation
def validate_schema(data, schema):
    for field, constraints in schema.items():
        if field not in data:
            raise ValidationTypeException(
                field=field,
                expected="required field",
                actual="missing"
            )
        
        value = data[field]
        expected_type = constraints.get('type')
        if expected_type and not isinstance(value, expected_type):
            raise ValidationTypeException(
                field=field,
                expected=expected_type.__name__,
                actual=type(value).__name__
            )
        
        # Range validation
        min_val = constraints.get('min')
        max_val = constraints.get('max')
        if min_val is not None and value < min_val:
            raise ValidationTypeException(
                field=field,
                expected=f">= {min_val}",
                actual=str(value)
            )
```

### InvalidPayloadException

::: WrenchCL.Exceptions.InvalidPayloadException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import InvalidPayloadException

def process_api_request(payload):
    required_fields = ['user_id', 'action', 'timestamp']
    missing_fields = [field for field in required_fields if field not in payload]
    
    if missing_fields:
        raise InvalidPayloadException(
            missing_fields=missing_fields,
            message=f"API request missing required fields: {', '.join(missing_fields)}"
        )
    
    # Process valid payload
    return process_user_action(payload)

def validate_batch_upload(payloads):
    errors = []
    for i, payload in enumerate(payloads):
        try:
            validate_single_payload(payload)
        except InvalidPayloadException as e:
            errors.append(f"Item {i}: {e}")
    
    if errors:
        raise InvalidPayloadException(
            message=f"Batch validation failed with {len(errors)} errors: {'; '.join(errors)}"
        )

# JSON API validation
def validate_json_api_payload(data):
    if not isinstance(data, dict):
        raise InvalidPayloadException(
            message="Payload must be a JSON object"
        )
    
    if 'data' not in data:
        raise InvalidPayloadException(
            missing_fields=['data'],
            message="JSON API payload must contain 'data' field"
        )
    
    data_section = data['data']
    required_data_fields = ['type', 'attributes']
    missing = [f for f in required_data_fields if f not in data_section]
    
    if missing:
        raise InvalidPayloadException(
            missing_fields=[f"data.{f}" for f in missing]
        )
```

## Miscellaneous Exceptions

### ReferenceNotFoundException

::: WrenchCL.Exceptions.ReferenceNotFoundException
    options:
      show_source: false
      heading_level: 4

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

class ResourceManager:
    def __init__(self):
        self._resources = {}
    
    def get_resource(self, resource_id):
        if resource_id not in self._resources:
            raise ReferenceNotFoundException(
                variable_name=f"resource[{resource_id}]",
                message=f"Resource with ID '{resource_id}' not found"
            )
        return self._resources[resource_id]

# Database lookup
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

::: WrenchCL.Exceptions.SecurityViolationException
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import SecurityViolationException

class SecurityManager:
    def validate_file_upload(self, filename, content):
        # Check file extension
        dangerous_extensions = ['.exe', '.bat', '.sh', '.php', '.jsp']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            raise SecurityViolationException(
                f"File type not allowed: {filename}"
            )
        
        # Check for suspicious content
        if b'<script>' in content.lower():
            raise SecurityViolationException(
                "File contains potentially malicious script content"
            )
    
    def validate_sql_query(self, query):
        # Basic SQL injection detection
        dangerous_patterns = ['DROP TABLE', 'DELETE FROM', '--', ';']
        query_upper = query.upper()
        
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                raise SecurityViolationException(
                    f"Query contains potentially dangerous pattern: {pattern}"
                )
    
    def check_rate_limit(self, user_id, action):
        if self.get_request_count(user_id, action) > self.get_rate_limit(action):
            raise SecurityViolationException(
                f"Rate limit exceeded for action: {action}"
            )

# Authentication example
def authenticate_user(token):
    if not token:
        raise SecurityViolationException("Authentication token required")
    
    if len(token) < 32:
        raise SecurityViolationException("Invalid token format")
    
    try:
        decoded = decode_jwt_token(token)
        if decoded['exp'] < time.time():
            raise SecurityViolationException("Token has expired")
    except Exception:
        raise SecurityViolationException("Invalid or corrupted token")
```

### GuardedResponseTrigger

::: WrenchCL.Exceptions.GuardedResponseTrigger
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Exceptions import GuardedResponseTrigger
import json

def lambda_handler(event, context):
    try:
        # Process the request
        result = process_lambda_request(event)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except ValidationError as e:
        # Early return with structured response
        response = {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Validation failed',
                'details': str(e)
            })
        }
        raise GuardedResponseTrigger(response)
        
    except AuthenticationError as e:
        response = {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Authentication required'})
        }
        raise GuardedResponseTrigger(response)

# Main Lambda wrapper
def handle_lambda_with_error_handling(handler_func):
    def wrapper(event, context):
        try:
            return handler_func(event, context)
        except GuardedResponseTrigger as e:
            # Extract and return the prepared response
            return e.get_response()
        except Exception as e:
            # Unhandled exception - return generic error
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal server error'})
            }
    return wrapper

@handle_lambda_with_error_handling
def my_lambda(event, context):
    # Your lambda logic here
    pass
```

## Exception Suggestion System

WrenchCL includes an intelligent exception suggestion system that provides helpful hints for common attribute errors:

```python
# The ExceptionSuggestor is automatically used by the logger
from WrenchCL import logger

class User:
    def __init__(self):
        self.username = "john"
        self.email = "john@example.com"
        self.profile_data = {}

user = User()

try:
    # Typo in attribute name
    print(user.usernme)  # Should be 'username'
except AttributeError as e:
    logger.error("Attribute error occurred", exc_info=True)
    # Output will include: "Did you mean: username?"

try:
    # Another typo
    print(user.emal)  # Should be 'email'
except AttributeError as e:
    logger.error("Another attribute error", exc_info=True)
    # Output will include: "Did you mean: email?"
```

## Best Practices

### Exception Chaining

```python
from WrenchCL.Exceptions import InvalidConfigurationException, InitializationException

def load_database_config():
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
            reason="Invalid JSON format in configuration"
        ) from e

def initialize_database():
    try:
        config = load_database_config()
        return connect_to_database(config)
    except InvalidConfigurationException as e:
        raise InitializationException(
            "Database initialization failed due to configuration error"
        ) from e
```

### Context-Aware Error Messages

```python
from WrenchCL.Exceptions import ValidationTypeException

class DataProcessor:
    def __init__(self, source_name):
        self.source_name = source_name
    
    def validate_record(self, record, line_number=None):
        context = f" in {self.source_name}"
        if line_number:
            context += f" at line {line_number}"
        
        try:
            self._validate_fields(record)
        except ValidationTypeException as e:
            # Add context to the error
            raise ValidationTypeException(
                field=e.args[0] if e.args else "unknown",
                expected="valid data",
                actual="invalid data",
                message=f"Validation failed{context}: {e}"
            ) from e
```

### Graceful Degradation

```python
from WrenchCL.Exceptions import InitializationException
from WrenchCL import logger

class ServiceWithFallback:
    def __init__(self):
        self.primary_service = None
        self.fallback_service = None
        
        try:
            self.primary_service = PrimaryService()
        except InitializationException as e:
            logger.warning(f"Primary service failed to initialize: {e}")
            
            try:
                self.fallback_service = FallbackService()
                logger.info("Using fallback service")
            except InitializationException as e:
                logger.error(f"Both services failed to initialize: {e}")
                raise InitializationException(
                    "No available service implementation"
                ) from e
    
    def process_data(self, data):
        if self.primary_service:
            return self.primary_service.process(data)
        elif self.fallback_service:
            return self.fallback_service.process(data)
        else:
            raise InitializationException("No service available")
```

### Error Recovery Patterns

```python
from WrenchCL.Exceptions import ArgumentValueException, ReferenceNotFoundException
from WrenchCL.Decorators import Retryable

class RobustDataManager:
    def __init__(self):
        self.cache = {}
        self.fallback_data = {}
    
    @Retryable(max_retries=3, delay=1)
    def get_data(self, key, use_cache=True):
        # Try cache first
        if use_cache and key in self.cache:
            return self.cache[key]
        
        try:
            # Try primary data source
            data = self.fetch_from_primary(key)
            self.cache[key] = data
            return data
            
        except ReferenceNotFoundException:
            # Try fallback data
            if key in self.fallback_data:
                logger.warning(f"Using fallback data for key: {key}")
                return self.fallback_data[key]
            
            # No data available
            raise ReferenceNotFoundException(
                variable_name=key,
                message=f"Data not found in primary or fallback sources: {key}"
            )
    
    def set_data(self, key, value):
        if not key:
            raise ArgumentValueException("Key cannot be empty")
        
        try:
            self.save_to_primary(key, value)
            self.cache[key] = value
        except Exception as e:
            # Save to fallback if primary fails
            logger.warning(f"Primary save failed, using fallback: {e}")
            self.fallback_data[key] = value
```

## Error Reporting and Monitoring

```python
from WrenchCL.Exceptions import *
from WrenchCL import logger

class ErrorReporter:
    def __init__(self):
        self.error_counts = {}
    
    def report_error(self, error, context=None):
        """Report and track errors for monitoring."""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_info = {
            'error_type': error_type,
            'error_message': str(error),
            'error_count': self.error_counts[error_type],
            'context': context
        }
        
        # Log based on error severity
        if isinstance(error, (SecurityViolationException, InitializationException)):
            logger.critical("Critical error occurred", extra=error_info, exc_info=True)
        elif isinstance(error, (InvalidConfigurationException, ValidationTypeException)):
            logger.error("Configuration or validation error", extra=error_info, exc_info=True)
        else:
            logger.warning("Recoverable error", extra=error_info)
    
    def get_error_summary(self):
        """Get summary of error occurrences."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts),
            'most_common': max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }

# Global error reporter instance
error_reporter = ErrorReporter()

# Usage in exception handlers
def safe_operation(data):
    try:
        return risky_operation(data)
    except Exception as e:
        error_reporter.report_error(e, context={'operation': 'safe_operation', 'data_type': type(data).__name__})
        raise
```