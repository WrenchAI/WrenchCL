# Tools and Utilities

WrenchCL provides a comprehensive collection of utility tools for data processing, validation, file handling, and type checking. These tools are designed to handle common programming tasks with robust error handling and flexible APIs.

## Overview

The Tools module includes:

- **Data Processing** - JSON parsing, serialization, and transformation
- **Type Safety** - Runtime type checking and validation  
- **File Operations** - File type detection, metadata extraction, and encoding
- **Functional Programming** - Maybe monad, coalescing, and data standardization
- **Image Processing** - Base64 encoding and validation

## Data Processing Tools

### JSON Parser

::: WrenchCL.Tools.parse_json
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import parse_json

# Parse nested JSON structures
complex_json = '''
{
    "user": {
        "profile": "{\\"name\\": \\"John\\", \\"age\\": 30}",
        "settings": "[{\\"theme\\": \\"dark\\"}]"
    }
}
'''

result = parse_json(complex_json, max_depth=10, verbose=True)
print(result['user']['profile']['name'])  # "John"

# Handle malformed JSON gracefully
malformed = '{"name": "John", "data": "{incomplete...'
result = parse_json(malformed, verbose=True)  # Handles partial parsing
```

### JSON Serialization

::: WrenchCL.Tools.robust_serializer
    options:
      show_source: false
      heading_level: 4

```python
import json
from datetime import datetime, date
from decimal import Decimal
from WrenchCL.Tools import robust_serializer

# Serialize complex objects
data = {
    "timestamp": datetime.now(),
    "birth_date": date.today(),
    "balance": Decimal("123.45"),
    "user": CustomUser(name="John")
}

json_string = json.dumps(data, default=robust_serializer, indent=2)
```

### Single Quote JSON Decoder

```python
from WrenchCL.Tools import single_quote_decoder
import json

# Handle JSON with single quotes (common in LLM outputs)
llm_output = "{'name': 'John', 'age': 30, 'active': true}"
data = json.loads(llm_output, cls=single_quote_decoder)
print(data['name'])  # "John"

# Also handles markdown code blocks
markdown_json = """
```json
{'users': [{'name': 'Alice'}, {'name': 'Bob'}]}
```
"""
data = json.loads(markdown_json, cls=single_quote_decoder)
```

## Type Checking and Validation

### TypeChecker

::: WrenchCL.Tools.typechecker
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import typechecker

# Single dictionary validation
user_data = {"name": "John", "age": 30, "email": "john@example.com"}
expected_types = {"name": str, "age": int, "email": str}

# Raises TypeError if validation fails
typechecker(user_data, expected_types, errors='raise')

# List of dictionaries validation
users = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": "invalid"}  # This will fail
]

try:
    typechecker(users, {"name": str, "age": int}, errors='raise')
except TypeError as e:
    print(f"Validation failed: {e}")

# Multiple type options
flexible_types = {"id": [int, str], "active": bool}
typechecker({"id": "123", "active": True}, flexible_types)  # Valid
typechecker({"id": 456, "active": True}, flexible_types)   # Also valid

# Allow None values
optional_types = {"name": str, "nickname": str}
typechecker(
    {"name": "John", "nickname": None}, 
    optional_types, 
    none_is_ok=True
)
```

### Data Standardization

::: WrenchCL.Tools.standardize_none
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import standardize_none
import pandas as pd

# Clean up messy data
messy_data = {
    "name": "John",
    "email": "",           # Empty string -> None
    "phone": "null",       # String "null" -> None  
    "address": "n/a",      # String "n/a" -> None
    "status": "active"
}

clean_data = standardize_none(messy_data)
# Result: {"name": "John", "email": None, "phone": None, "address": None, "status": "active"}

# Work with DataFrames
df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "", "Bob"], 
    "status": ["active", "null", "pending"]
})

clean_df = standardize_none(df)
print(clean_df['name'].isna().sum())  # Shows count of None values

# Custom none-like values
custom_none_values = {"", "NULL", "missing", "undefined"}
result = standardize_none(data, none_like_values=custom_none_values)
```

## Functional Programming Tools

### Maybe Monad

::: WrenchCL.Tools.Maybe
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import Maybe

# Safe nested access
user_data = {
    "profile": {
        "contact": {
            "email": "john@example.com"
        }
    }
}

# Traditional approach (risky)
try:
    email = user_data['profile']['contact']['email']
except KeyError:
    email = None

# Maybe approach (safe)
email = Maybe(user_data).get('profile').get('contact').get('email').out()

# Chain operations safely
result = (Maybe(user_data)
    .get('profile')
    .get('contact')
    .get('email')
    .upper()          # String method
    .replace('@', '_at_')
    .out())

print(result)  # "JOHN_AT_EXAMPLE.COM" or None if any step fails

# Built-in function support
numbers = [1, 2, 3, 4, 5]
total = Maybe(numbers).sum().out()  # 15

# Context manager for chaining
with Maybe(user_data) as m:
    email = m.get('profile').get('contact').get('email')
    domain = email.split('@').get(1) if email.value else None
```

### Coalesce Function

::: WrenchCL.Tools.coalesce
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import coalesce

# Return first non-None value
name = coalesce(None, "", "John", "Default")  # Returns ""
name = coalesce(None, None, "John", "Default")  # Returns "John"

# Configuration with fallbacks
config_value = coalesce(
    os.getenv('API_KEY'),           # Environment variable
    config.get('api_key'),          # Config file
    "default-key"                   # Fallback
)

# Database field handling
user_display_name = coalesce(
    user.display_name,
    user.full_name,
    user.username,
    f"User {user.id}"
)

# Form data processing
email = coalesce(
    form_data.get('email'),
    user_profile.email,
    user_account.backup_email,
    None
)
```

## File and Image Tools

### File Type Detection

::: WrenchCL.Tools.get_file_type
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import get_file_type

# Detect file type from various sources
extension, mime_type = get_file_type("https://example.com/image.jpg", is_url=True)
print(f"Extension: {extension}, MIME: {mime_type}")  # .jpg, image/jpeg

# Local file
extension, mime_type = get_file_type("/path/to/document.pdf", is_url=False)

# Base64 encoded content
base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
extension, mime_type = get_file_type(base64_data)

# Raw bytes
with open("image.png", "rb") as f:
    file_bytes = f.read()
extension, mime_type = get_file_type(file_bytes)

# BytesIO object
from io import BytesIO
buffer = BytesIO(file_bytes)
extension, mime_type = get_file_type(buffer)
```

### Image to Base64

::: WrenchCL.Tools.image_to_base64
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import image_to_base64, validate_base64, get_hash

# Convert image to base64
base64_string = image_to_base64("https://example.com/image.jpg", is_url=True)

# Local file with hash
base64_string, file_hash = image_to_base64(
    "/path/to/image.png", 
    is_url=False, 
    return_hash=True
)
print(f"Hash: {file_hash}")

# Validate base64 string
is_valid = validate_base64(base64_string)
print(f"Valid base64: {is_valid}")

# Get hash of any data
data_hash = get_hash(b"Hello, World!")
string_hash = get_hash("Text data")
```

### File Metadata

::: WrenchCL.Tools.get_metadata
    options:
      show_source: false
      heading_level: 4

```python
from WrenchCL.Tools import get_metadata

# URL metadata
metadata = get_metadata("https://example.com/document.pdf", is_url=True)
print(metadata)
# {
#     'content_type': 'application/pdf',
#     'content_length': '1048576',
#     'last_modified': datetime.datetime(2024, 1, 15, 10, 30, 0),
#     'url': 'https://example.com/document.pdf'
# }

# Local file metadata
metadata = get_metadata("/path/to/file.txt", is_url=False)
print(metadata)
# {
#     'file_path': '/path/to/file.txt',
#     'file_size': 1024,
#     'creation_time': '2024-01-15T10:30:00',
#     'mime_type': 'text/plain'
# }
```

## Advanced Usage Examples

### Data Processing Pipeline

```python
from WrenchCL.Tools import parse_json, typechecker, standardize_none, Maybe

def process_api_response(response_text):
    """Process complex API response with nested JSON."""
    
    # Parse potentially nested JSON
    data = parse_json(response_text, max_depth=15, verbose=True)
    
    # Validate structure
    expected_schema = {
        "users": list,
        "metadata": dict,
        "status": str
    }
    typechecker(data, expected_schema, errors='raise')
    
    # Clean up None-like values
    clean_data = standardize_none(data)
    
    # Safe extraction of nested data
    users = []
    for user_data in clean_data.get('users', []):
        user = {
            'id': Maybe(user_data).get('id').out(),
            'name': Maybe(user_data).get('profile').get('name').out(),
            'email': Maybe(user_data).get('contact').get('email').out(),
            'active': Maybe(user_data).get('status').get('active').out()
        }
        users.append(user)
    
    return users
```

### Configuration Management

```python
from WrenchCL.Tools import coalesce, Maybe
import os
import json

class ConfigManager:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from multiple sources."""
        file_config = {}
        if self.config_file:
            try:
                with open(self.config_file) as f:
                    file_config = json.load(f)
            except FileNotFoundError:
                pass
        
        self._config = file_config
    
    def get(self, key, default=None):
        """Get configuration value with fallbacks."""
        return coalesce(
            os.getenv(key.upper()),           # Environment variable
            Maybe(self._config).get(key).out(),  # Config file
            default                           # Default value
        )
    
    def get_database_url(self):
        """Get database URL with multiple fallback options."""
        return coalesce(
            os.getenv('DATABASE_URL'),
            self.get('database_url'),
            f"postgresql://{self.get('db_user')}:{self.get('db_password')}@{self.get('db_host')}/{self.get('db_name')}",
            "sqlite:///default.db"
        )

# Usage
config = ConfigManager('config.json')
db_url = config.get_database_url()
api_key = config.get('api_key', 'default-key')
```

### File Processing Utility

```python
from WrenchCL.Tools import get_file_type, image_to_base64, get_metadata
import os

class FileProcessor:
    def __init__(self):
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        self.supported_doc_types = {'.pdf', '.doc', '.docx', '.txt'}
    
    def process_file(self, file_path_or_url, is_url=False):
        """Process file and return structured information."""
        
        # Get file type and metadata
        try:
            extension, mime_type = get_file_type(file_path_or_url, is_url=is_url)
            metadata = get_metadata(file_path_or_url, is_url=is_url)
        except Exception as e:
            return {'error': f'Failed to process file: {e}'}
        
        result = {
            'extension': extension,
            'mime_type': mime_type,
            'metadata': metadata,
            'type_category': self._categorize_file(extension)
        }
        
        # Process images
        if extension.lower() in self.supported_image_types:
            try:
                base64_data, file_hash = image_to_base64(
                    file_path_or_url, 
                    is_url=is_url, 
                    return_hash=True
                )
                result.update({
                    'base64_data': base64_data[:100] + '...',  # Truncated for display
                    'file_hash': file_hash,
                    'size_estimate': len(base64_data) * 3 // 4  # Approximate original size
                })
            except Exception as e:
                result['processing_error'] = str(e)
        
        return result
    
    def _categorize_file(self, extension):
        """Categorize file by extension."""
        if extension.lower() in self.supported_image_types:
            return 'image'
        elif extension.lower() in self.supported_doc_types:
            return 'document'
        else:
            return 'other'

# Usage
processor = FileProcessor()

# Process URL
result = processor.process_file('https://example.com/image.jpg', is_url=True)
print(f"File type: {result['type_category']}")

# Process local file
result = processor.process_file('/path/to/document.pdf', is_url=False)
```

### Data Validation Framework

```python
from WrenchCL.Tools import typechecker, standardize_none
from typing import List, Dict, Any

class DataValidator:
    def __init__(self):
        self.validation_rules = {}
    
    def add_rule(self, name: str, schema: Dict[str, Any]):
        """Add validation rule."""
        self.validation_rules[name] = schema
    
    def validate(self, data: Any, rule_name: str, clean_data: bool = True) -> Dict[str, Any]:
        """Validate data against named rule."""
        if rule_name not in self.validation_rules:
            raise ValueError(f"Unknown validation rule: {rule_name}")
        
        schema = self.validation_rules[rule_name]
        
        # Clean data if requested
        if clean_data:
            data = standardize_none(data)
        
        # Validate
        try:
            typechecker(data, schema, errors='raise', verbose=False)
            return {'valid': True, 'data': data, 'errors': []}
        except TypeError as e:
            return {'valid': False, 'data': data, 'errors': [str(e)]}
    
    def validate_batch(self, data_list: List[Any], rule_name: str) -> Dict[str, Any]:
        """Validate multiple items."""
        results = []
        for i, item in enumerate(data_list):
            result = self.validate(item, rule_name)
            result['index'] = i
            results.append(result)
        
        valid_count = sum(1 for r in results if r['valid'])
        return {
            'total': len(results),
            'valid': valid_count,
            'invalid': len(results) - valid_count,
            'results': results
        }

# Usage
validator = DataValidator()

# Define schemas
validator.add_rule('user', {
    'id': int,
    'name': str,
    'email': str,
    'age': [int, type(None)],  # Optional
    'active': bool
})

validator.add_rule('product', {
    'sku': str,
    'name': str,
    'price': [int, float],
    'categories': list
})

# Validate single item
user_data = {
    'id': 123,
    'name': 'John Doe',
    'email': 'john@example.com',
    'age': None,
    'active': True
}

result = validator.validate(user_data, 'user')
print(f"Valid: {result['valid']}")

# Validate batch
users = [
    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'active': True},
    {'id': 'invalid', 'name': 'Bob', 'email': 'bob@example.com', 'active': True},
    {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com', 'active': 'yes'}
]

batch_result = validator.validate_batch(users, 'user')
print(f"Batch validation: {batch_result['valid']}/{batch_result['total']} valid")
```

## Performance Tips

### Efficient JSON Processing

```python
# For large JSON data, limit recursion depth
result = parse_json(large_json_string, max_depth=5)

# Use show_json_tree for debugging structure
parse_json(data, print_tree=True)  # Shows structure without processing
```

### Type Checking Optimization

```python
# Check if validation is needed before expensive operations
if not typechecker(data, schema, errors='coerce'):
    # Handle invalid data
    clean_data = sanitize_data(data)
else:
    # Data is valid, proceed
    process_data(data)
```

### Maybe Monad Patterns

```python
# Efficient chaining
result = (Maybe(data)
    .get('key1')
    .get('key2') 
    .out())

# Avoid excessive chaining for simple cases
if data and 'key' in data:
    value = data['key']  # Simpler than Maybe for basic cases
```