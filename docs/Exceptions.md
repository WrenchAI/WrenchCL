# Exceptions Module Documentation

The Exceptions module provides a comprehensive hierarchy of custom exceptions and utilities for better error handling, debugging, and user experience.

## Overview

- **Custom Exception Hierarchy**: Specialized exceptions for different error scenarios
- **GuardedResponseTrigger**: Lambda response control flow mechanism  
- **ExceptionSuggestor**: Intelligent error suggestions for common mistakes
- **Context-Aware Errors**: Rich error information for debugging

---

## Custom Exception Hierarchy

### Core Application Exceptions

#### IncompleteInitializationException
Raised when an object is used before proper initialization.

```python
from WrenchCL.Exceptions import IncompleteInitializationException

class DatabaseService:
    def __init__(self):
        self.connection = None
        self.initialized = False
    
    def initialize(self, connection_string):
        self.connection = create_connection(connection_string)
        self.initialized = True
    
    def query(self, sql):
        if not self.initialized:
            raise IncompleteInitializationException(
                "DatabaseService must be initialized before use. Call initialize() first."
            )
        return self.connection.execute(sql)

# Usage
db = DatabaseService()
# db.query("SELECT * FROM users")  # Raises IncompleteInitializationException
db.initialize("postgresql://localhost/mydb")
db.query("SELECT * FROM users")  # Works
```

#### InitializationException
Raised when an object cannot be properly initialized.

```python
from WrenchCL.Exceptions import InitializationException

class ConfigManager:
    def __init__(self, config_path):
        try:
            self.config = self._load_config(config_path)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
            raise InitializationException(
                f"Failed to initialize ConfigManager: {str(e)}"
            ) from e
    
    def _load_config(self, path):
        # Configuration loading logic
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        # ... load and parse config
```

### Validation Exceptions

#### ArgumentTypeException
Raised when arguments of invalid types are passed.

```python
from WrenchCL.Exceptions import ArgumentTypeException

def process_user_data(user_id, data):
    if not isinstance(user_id, int):
        raise ArgumentTypeException(
            f"user_id must be an integer, got {type(user_id).__name__}"
        )
    
    if not isinstance(data, dict):
        raise ArgumentTypeException(
            f"data must be a dictionary, got {type(data).__name__}"
        )
    
    # Process the data
    return f"Processed user {user_id}"

# Usage
try:
    process_user_data("123", {"name": "John"})  # Raises ArgumentTypeException
except ArgumentTypeException as e:
    print(f"Type error: {e}")
```

#### ArgumentValueException
Raised when arguments have invalid values.

```python
from WrenchCL.Exceptions import ArgumentValueException

def set_user_age(age):
    if not isinstance(age, int):
        raise ArgumentTypeException("Age must be an integer")
    
    if age < 0 or age > 150:
        raise ArgumentValueException(
            f"Age must be between 0 and 150, got {age}"
        )
    
    return f"Age set to {age}"

# Usage
try:
    set_user_age(-5)  # Raises ArgumentValueException
except ArgumentValueException as e:
    print(f"Value error: {e}")
```

#### ValidationTypeException
Advanced validation with field-specific context.

```python
from WrenchCL.Exceptions