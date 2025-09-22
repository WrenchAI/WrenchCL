# Tools

WrenchCL Tools provide utilities for data processing, validation, and file handling.

## Import Structure

```python
# Individual functions
from WrenchCL.Tools import coalesce, Maybe, typechecker

# Or access via module
import WrenchCL.Tools as tools
result = tools.coalesce(None, "default")
```

## Core Utilities

### coalesce()

Returns the first non-None value:

```python
from WrenchCL.Tools import coalesce

# Basic usage
name = coalesce(None, "", "John")  # Returns ""
name = coalesce(None, None, "John")  # Returns "John"

# Configuration fallbacks
api_key = coalesce(
    os.getenv('API_KEY'),
    config.get('api_key'),
    "default-key"
)
```

### Maybe

Safe nested attribute/key access:

```python
from WrenchCL.Tools import Maybe

# Safe nested access
data = {"user": {"profile": {"email": "john@example.com"}}}

# Instead of try/except blocks:
email = Maybe(data).get('user').get('profile').get('email').out()

# Chain operations safely
result = (Maybe(data)
    .get('user')
    .get('profile') 
    .get('email')
    .upper()
    .replace('@', '_at_')
    .out())

# Context manager for chaining
with Maybe(data) as m:
    email = m.get('user').get('profile').get('email').out()
```

### typechecker()

Runtime type validation:

```python
from WrenchCL.Tools import typechecker

# Single dict validation
user = {"name": "John", "age": 30}
types = {"name": str, "age": int}

typechecker(user, types, errors='raise')  # Raises TypeError if invalid

# Multiple type options
flexible = {"id": [int, str], "active": bool}
typechecker({"id": "123", "active": True}, flexible)  # Valid

# Allow None values
typechecker(
    {"name": "John", "nickname": None}, 
    {"name": str, "nickname": str},
    none_is_ok=True
)

# List of dicts
users = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
typechecker(users, {"name": str, "age": int})
```

## Data Processing

### standardize_none()

Clean up messy None-like values:

```python
from WrenchCL.Tools import standardize_none

# Clean various None representations
data = {
    "name": "John",
    "email": "",        # -> None
    "phone": "null",    # -> None
    "status": "n/a"     # -> None
}

clean = standardize_none(data)
# Result: {"name": "John", "email": None, "phone": None, "status": None}

# Works with DataFrames too
import pandas as pd
df = pd.DataFrame({"col": ["", "null", "valid"]})
clean_df = standardize_none(df)
```

### JSON Utilities

```python
from WrenchCL.Tools import (
    parse_json, safe_json_loader, list_loader, show_json_tree,
    robust_serializer, single_quote_decoder
)
import json

# Parse nested JSON
nested_json = '{"user": "{\\"name\\": \\"John\\"}"}'
result = parse_json(nested_json)
print(result['user']['name'])  # "John"

# Show JSON structure without processing
show_json_tree({"nested": {"data": "here"}})

# Lower-level parsing functions
safe_data = safe_json_loader('{"key": "value"}')
list_data = list_loader(['{"item": 1}', '{"item": 2}'])

# Robust serialization
from datetime import datetime
data = {"timestamp": datetime.now(), "value": 123}
json_str = json.dumps(data, default=robust_serializer)

# Handle single quotes (from LLMs)
llm_output = "{'name': 'John', 'age': 30}"
parsed = json.loads(llm_output, cls=single_quote_decoder)
```

## File Utilities

### File Type Detection

```python
from WrenchCL.Tools import get_file_type

# Various input types
ext, mime = get_file_type("https://example.com/image.jpg", is_url=True)
ext, mime = get_file_type("/path/to/file.pdf", is_url=False)
ext, mime = get_file_type(bytes_data)
```

### Image Processing

```python
from WrenchCL.Tools import image_to_base64, validate_base64

# Convert to base64
b64_string = image_to_base64("image.jpg", is_url=False)
b64_string, hash_val = image_to_base64("image.jpg", return_hash=True)

# Validate base64
is_valid = validate_base64(b64_string)
```

### File Metadata

```python
from WrenchCL.Tools import get_metadata

# URL metadata
metadata = get_metadata("https://example.com/file.pdf", is_url=True)
# Returns: content_type, content_length, last_modified, url

# Local file metadata
metadata = get_metadata("/path/file.txt", is_url=False)  
# Returns: file_path, file_size, creation_time, mime_type
```

## Practical Examples

### Safe Configuration Loading

```python
from WrenchCL.Tools import Maybe, coalesce

def get_database_config(config_dict):
    return {
        'host': coalesce(
            os.getenv('DB_HOST'),
            Maybe(config_dict).get('database').get('host').out(),
            'localhost'
        ),
        'port': coalesce(
            os.getenv('DB_PORT'),
            Maybe(config_dict).get('database').get('port').out(), 
            5432
        )
    }
```

### Data Validation Pipeline

```python
from WrenchCL.Tools import typechecker, standardize_none

def validate_user_data(raw_data):
    # Clean None-like values
    clean_data = standardize_none(raw_data)
    
    # Validate types
    schema = {
        'name': str,
        'age': [int, type(None)],  # Optional
        'email': str,
        'active': bool
    }
    
    try:
        typechecker(clean_data, schema, errors='raise')
        return {'valid': True, 'data': clean_data}
    except TypeError as e:
        return {'valid': False, 'error': str(e)}
```

### File Processing

```python
from WrenchCL.Tools import get_file_type, get_metadata, image_to_base64

def process_upload(file_path):
    # Get file info
    ext, mime_type = get_file_type(file_path, is_url=False)
    metadata = get_metadata(file_path, is_url=False)
    
    result = {
        'extension': ext,
        'mime_type': mime_type,
        'size': metadata['file_size']
    }
    
    # Process images
    if ext.lower() in ['.jpg', '.png', '.gif']:
        b64_data, file_hash = image_to_base64(file_path, return_hash=True)
        result.update({
            'base64': b64_data,
            'hash': file_hash
        })
    
    return result
```

All tools handle errors gracefully and provide detailed error messages when operations fail.