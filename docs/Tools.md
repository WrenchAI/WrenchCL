# Tools Module Documentation

The Tools module provides a collection of utility functions for data processing, validation, serialization, and common programming patterns.

## Overview

- **Data Processing**: JSON parsing, serialization, type checking
- **File Operations**: Image encoding, file type detection, metadata extraction  
- **Utility Patterns**: Maybe monad, coalescing, null standardization
- **Type Safety**: Robust type checking and validation

---

## JSON Processing

### parse_json

Recursively parses nested JSON structures with depth protection and intelligent type handling.

```python
from WrenchCL.Tools import parse_json

# Parse complex nested JSON
response = {
    "data": '{"users": "[{\\"id\\": 1, \\"profile\\": \\"{\\\\\\"name\\\\\\": \\\\\\"John\\\\\\"}\\"}, \\"raw_string\\"]"}',
    "meta": '{"total": 150}'
}

parsed = parse_json(response, max_depth=10, verbose=True)
# Automatically handles multiple levels of JSON encoding
```

**Features:**
- **Recursive Parsing**: Handles deeply nested JSON structures
- **Depth Protection**: Prevents infinite recursion with configurable max depth
- **Mixed Data Types**: Handles JSON strings mixed with other data types
- **Error Recovery**: Gracefully handles malformed JSON
- **Debug Visualization**: Optional tree view of parsed structure

**Advanced Usage:**
```python
# Parse with tree visualization
parsed = parse_json(complex_response, print_tree=True)

# Custom depth limit for performance
parsed = parse_json(data, max_depth=5)

# Handle recursive structures safely
try:
    parsed = parse_json(potentially_cyclic_data, max_depth=25)
except RecursionError:
    logger.error("Data structure too deep or contains cycles")
```

### safe_json_loader

Safely loads JSON with graceful error handling for malformed data.

```python
from WrenchCL.Tools import safe_json_loader

# Load valid JSON
data = safe_json_loader('{"valid": "json"}')

# Handle malformed JSON gracefully  
malformed = safe_json_loader('{"missing": "end_brace"')
# Returns the original string instead of raising an exception

# Strict mode for validation
try:
    data = safe_json_loader(user_input, raise_error=True)
except json.JSONDecodeError:
    handle_invalid_input()
```

### list_loader

Processes lists containing mixed JSON and non-JSON elements.

```python
from WrenchCL.Tools import list_loader

mixed_list = [
    '{"id": 1, "data": "{\\"nested\\": \\"value\\"}"}',
    "plain string",
    {"already": "parsed"},
    '["nested", "array"]'
]

processed = list_loader(mixed_list)
# Recursively parses JSON strings while preserving other types
```

---

## Data Serialization

### robust_serializer

JSON serializer that handles complex Python objects including datetime, Decimal, and custom classes.

```python
from WrenchCL.Tools import robust_serializer
import json
from datetime import datetime
from decimal import Decimal

data = {
    "timestamp": datetime.now(),
    "amount": Decimal("123.45"),
    "user": CustomUserObject(name="Alice"),
    "tags": {"development", "testing"}  # Set object
}

json_string = json.dumps(data, default=robust_serializer, indent=2)
```

**Supported Types:**
- `datetime` and `date` → ISO 8601 strings
- `Decimal` → float
- Objects with `__dict__` → dictionary representation
- All other types → string representation

### single_quote_decoder

Custom JSON decoder for handling LLM-generated JSON with single quotes and markdown.

```python
from WrenchCL.Tools import single_quote_decoder
import json

# Handle LLM output with single quotes
llm_json = """
```json
{'name': 'John', 'data': {'nested': 'value'}}
```
"""

data = json.loads(llm_json, cls=single_quote_decoder)
# Automatically handles markdown blocks and single quotes
```

**Features:**
- Removes markdown code block markers
- Converts single quotes to double quotes
- Handles escaped quotes properly
- Sanitizes unescaped quotes automatically

---

## Type Checking & Validation

### typechecker

Robust type validation for dictionaries and lists with detailed error reporting.

```python
from WrenchCL.Tools import typechecker

# Define expected schema
schema = {
    "name": str,
    "age": int,
    "email": str,
    "active": bool,
    "tags": list,
    "metadata": [dict, type(None)]  # Multiple allowed types
}

# Validate single record
user_data = {"name": "Alice", "age": 30, "email": "alice@example.com", "active": True, "tags": ["user"], "metadata": None}

is_valid = typechecker(user_data, schema, none_is_ok=True)

# Validate batch data
users = [
    {"name": "Bob", "age": 25, "email": "bob@example.com", "active": True, "tags": [], "metadata": {}},
    {"name": "Charlie", "age": "invalid", "email": "charlie@example.com", "active": True, "tags": [], "metadata": {}}
]

try:
    typechecker(users, schema, errors='raise')
except TypeError as e:
    print(f"Validation failed: {e}")
    # TypeError: Incorrect param types: 'age' is str, expected int
```

**Validation Modes:**
- `errors='raise'`: Raise TypeError on validation failure
- `errors='coerce'`: Return False on validation failure  
- `none_is_ok=True`: Allow None values for any field

### standardize_none

Converts various null-like values to proper Python None.

```python
from WrenchCL.Tools import standardize_none

# Clean messy data
messy_data = {
    "name": "Alice",
    "middle_name": "",
    "last_login": "null",
    "preferences": "undefined",
    "avatar": "n/a",
    "bio": "   ",
    "tags": ["valid", "", "none", "active"]
}

clean_data = standardize_none(messy_data)
# Converts '', 'null', 'undefined', 'n/a', '   ' to None

# Works with DataFrames (if pandas available)
import pandas as pd
df = pd.DataFrame({"col1": ["valid", "", "null"], "col2": [1, 2, "n/a"]})
clean_df = standardize_none(df)

# Custom null-like values
custom_clean = standardize_none(data, none_like_values={"", "missing", "unknown"})
```

---

## File Operations

### image_to_base64

Convert images from various sources to Base64 encoding with optional hashing.

```python
from WrenchCL.Tools import image_to_base64

# From URL
base64_data = image_to_base64("https://example.com/image.jpg", is_url=True)

# From local file
base64_data = image_to_base64("/path/to/image.png", is_url=False)

# With SHA-1 hash for deduplication
base64_data, hash_value = image_to_base64("/path/to/image.jpg", is_url=False, return_hash=True)

# Validate existing Base64
from WrenchCL.Tools import validate_base64
is_valid = validate_base64(base64_string)
```

### get_file_type

Intelligent file type detection from multiple sources.

```python
from WrenchCL.Tools import get_file_type

# From URL
extension, mime_type = get_file_type("https://example.com/document.pdf")

# From file path
extension, mime_type = get_file_type("/path/to/file.jpg", is_url=False)

# From Base64 data
extension, mime_type = get_file_type(base64_string, is_url=False)

# From bytes
extension, mime_type = get_file_type(byte_data, is_url=False)

# From BytesIO
from io import BytesIO
extension, mime_type = get_file_type(BytesIO(data), is_url=False)
```

### get_metadata

Extract comprehensive metadata from files and URLs.

```python
from WrenchCL.Tools import get_metadata

# URL metadata
metadata = get_metadata("https://example.com/file.pdf", is_url=True)
# Returns: content_type, content_length, last_modified, url

# File metadata
metadata = get_metadata("/path/to/file.txt", is_url=False)
# Returns: file_path, file_size, creation_time, mime_type
```

---

## Utility Patterns

### coalesce

Return the first non-None value from a sequence of arguments.

```python
from WrenchCL.Tools import coalesce

# Basic usage
result = coalesce(None, None, "first_value", "second_value")  # Returns "first_value"

# Configuration with fallbacks
config_value = coalesce(
    os.getenv("CUSTOM_SETTING"),
    user_preferences.get("setting"),
    default_settings["setting"],
    "hardcoded_fallback"
)

# Database field handling
display_name = coalesce(user.nickname, user.first_name, user.email, "Anonymous")
```

### Maybe

Monad pattern for safe chaining of operations that might fail.

```python
from WrenchCL.Tools import Maybe

# Safe chaining with automatic None handling
result = Maybe(user_data).get('profile').get('address').get('city').end_maybe()
# Returns None if any step in the chain fails

# Context manager for extended chaining
with Maybe(api_response) as maybe:
    city = maybe.get('data').get('user').get('location').get('city')
    country = maybe.get('data').get('user').get('location').get('country')
# Both operations benefit from safe chaining

# Built-in function support
numbers = Maybe([1, 2, 3, 4, 5])
with numbers as m:
    result = m.map(lambda x: x * 2).filter(lambda x: x > 5).list()
# Safe functional programming operations
```

**Aliases for `end_maybe()`:**
- `get_value()`, `resolve()`, `extract()`, `result()`, `done()`, `value()`, `exit()`, `out()`, `chain_break()`

---

## Advanced Examples

### Complex Data Processing Pipeline

```python
from WrenchCL.Tools import parse_json, typechecker, standardize_none, robust_serializer
import json

def process_api_response(raw_response):
    """Complete data processing pipeline."""
    
    # 1. Parse complex nested JSON
    parsed_data = parse_json(raw_response, max_depth=15)
    
    # 2. Standardize null values
    clean_data = standardize_none(parsed_data)
    
    # 3. Validate data structure
    schema = {
        "users": list,
        "metadata": dict,
        "timestamp": str
    }
    
    if not typechecker(clean_data, schema, none_is_ok=True):
        raise ValueError("Invalid data structure")
    
    # 4. Process users with safety
    processed_users = []
    for user in clean_data.get("users", []):
        safe_user = Maybe(user)
        processed_user = {
            "id": safe_user.get("id").end_maybe(),
            "name": coalesce(
                safe_user.get("display_name").end_maybe(),
                safe_user.get("full_name").end_maybe(), 
                safe_user.get("username").end_maybe(),
                "Anonymous"
            ),
            "email": safe_user.get("contact").get("email").end_maybe()
        }
        processed_users.append(processed_user)
    
    # 5. Return serializable result
    result = {
        "users": processed_users,
        "processed_at": datetime.now(),
        "total_count": len(processed_users)
    }
    
    return json.dumps(result, default=robust_serializer, indent=2)
```

### File Processing with Type Detection

```python
from WrenchCL.Tools import get_file_type, image_to_base64, get_metadata
from WrenchCL.Connect import S3ServiceGateway

def process_uploaded_file(file_source, is_url=True):
    """Complete file processing workflow."""
    
    # 1. Detect file type and validate
    try:
        extension, mime_type = get_file_type(file_source, is_url=is_url)
    except UnsupportedFileTypeError:
        raise ValueError("Unsupported file type")
    
    # 2. Get file metadata
    metadata = get_metadata(file_source, is_url=is_url)
    
    # 3. Process based on file type
    if mime_type.startswith('image/'):
        # Convert to Base64 with hash for deduplication
        base64_data, file_hash = image_to_base64(
            file_source, 
            is_url=is_url, 
            return_hash=True
        )
        
        # Upload to S3 with hash-based naming
        s3 = S3ServiceGateway()
        object_key = f"images/{file_hash}{extension}"
        
        s3_url = s3.upload_file(
            file=base64_data,
            bucket_name="processed-files",
            object_key=object_key,
            return_url=True
        )
        
        return {
            "type": "image",
            "s3_url": s3_url,
            "hash": file_hash,
            "metadata": metadata
        }
    
    else:
        # Handle other file types
        return {
            "type": "document", 
            "mime_type": mime_type,
            "metadata": metadata
        }
```

### Robust API Data Validation

```python
from WrenchCL.Tools import typechecker, standardize_none, Maybe

def validate_user_registration(data):
    """Comprehensive user registration validation."""
    
    # Clean the data first
    clean_data = standardize_none(data)
    
    # Define schema with multiple allowed types
    schema = {
        "email": str,
        "password": str,
        "age": [int, type(None)],
        "preferences": [dict, type(None)],
        "marketing_consent": bool,
        "referral_code": [str, type(None)]
    }
    
    # Validate basic structure
    if not typechecker(clean_data, schema, none_is_ok=True, errors='raise'):
        raise ValueError("Invalid data structure")
    
    # Advanced validation with Maybe for safety
    email = Maybe(clean_data).get('email').end_maybe()
    if not email or '@' not in email:
        raise ValueError("Invalid email address")
    
    # Validate nested preferences safely
    prefs = Maybe(clean_data).get('preferences')
    if prefs.end_maybe():
        pref_schema = {
            "theme": [str, type(None)],
            "notifications": [bool, type(None)],
            "language": [str, type(None)]
        }
        typechecker(prefs.end_maybe(), pref_schema, none_is_ok=True, errors='raise')
    
    return clean_data
```

---

## Performance Tips

### JSON Processing
```python
# For large datasets, limit recursion depth
large_data = parse_json(response, max_depth=5)  # Faster parsing

# Use safe_json_loader for simple validation
simple_check = safe_json_loader(user_input, raise_error=False)
if isinstance(simple_check, str):
    # Handle invalid JSON without exceptions
    pass
```

### Type Checking
```python
# Batch validation is more efficient than individual checks
all_valid = typechecker(list_of_records, schema, errors='coerce')

# Use specific type unions instead of broad validation
efficient_schema = {
    "id": int,  # More specific than [int, str, type(None)]
    "status": str
}
```

### File Operations
```python
# Cache file type detection results
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_file_type(file_path):
    return get_file_type(file_path, is_url=False)

# Use BytesIO for in-memory file operations
from io import BytesIO
buffer = BytesIO(file_data)
file_type = get_file_type(buffer, is_url=False)
```

---

## Error Handling Best Practices

### Graceful Degradation
```python
from WrenchCL.Tools import Maybe, coalesce

def safe_data_extraction(response):
    """Extract data with multiple fallbacks."""
    
    # Try multiple extraction methods
    data = coalesce(
        Maybe(response).get('data').get('primary').end_maybe(),
        Maybe(response).get('fallback_data').end_maybe(),
        Maybe(response).get('cached_data').end_maybe(),
        {}  # Empty dict as final fallback
    )
    
    return data
```

### Validation with Recovery
```python
def process_with_recovery(data_list):
    """Process list with error recovery."""
    
    valid_records = []
    errors = []
    
    for i, record in enumerate(data_list):
        try:
            # Clean and validate
            clean_record = standardize_none(record)
            if typechecker(clean_record, schema, errors='raise'):
                valid_records.append(clean_record)
        except (TypeError, ValueError) as e:
            errors.append({"index": i, "error": str(e), "record": record})
    
    return {
        "valid_records": valid_records,
        "errors": errors,
        "success_rate": len(valid_records) / len(data_list)
    }
```

---

## Integration Examples

### With Logger
```python
from WrenchCL.Tools import logger, parse_json, typechecker

def process_api_data(response):
    """Process API response with detailed logging."""
    
    logger.info("Starting API response processing")
    
    try:
        # Parse with logging
        parsed = parse_json(response, verbose=True)
        logger.data(parsed)  # Beautiful data visualization
        
        # Validate with logging
        if typechecker(parsed, schema, verbose=True):
            logger.success("Data validation passed")
            return parsed
        else:
            logger.warning("Data validation failed")
            return None
            
    except Exception as e:
        logger.error("Processing failed", e)
        raise
```

### With AWS Services
```python
from WrenchCL.Tools import image_to_base64, robust_serializer
from WrenchCL.Connect import S3ServiceGateway, RdsServiceGateway
import json

def store_user_avatar(user_id, image_url):
    """Complete user avatar processing pipeline."""
    
    # Convert image to base64
    base64_data, image_hash = image_to_base64(image_url, return_hash=True)
    
    # Upload to S3
    s3 = S3ServiceGateway()
    s3_key = f"avatars/{user_id}/{image_hash}.jpg"
    s3_url = s3.upload_file(base64_data, "user-assets", s3_key, return_url=True)
    
    # Update database with serializable data
    rds = RdsServiceGateway()
    update_data = {
        "avatar_url": s3_url,
        "avatar_hash": image_hash,
        "updated_at": datetime.now()
    }
    
    rds.update_database(
        "UPDATE users SET avatar_data = %s WHERE id = %s",
        payload=(json.dumps(update_data, default=robust_serializer), user_id)
    )
    
    return s3_url
```

The Tools module provides a comprehensive set of utilities that work seamlessly together to handle complex data processing, validation, and file operations with robust error handling and type safety.