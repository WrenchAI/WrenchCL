# Decorators Module Documentation

The Decorators module provides production-ready decorators for common patterns including retry logic, singleton enforcement, thread synchronization, and deprecation warnings.

## Overview

- **Retryable**: Intelligent retry logic for network operations and AWS services
- **SingletonClass**: Thread-safe singleton pattern enforcement  
- **Synchronized**: Method-level thread synchronization
- **Deprecated**: Clean deprecation warnings with tracking

---

## Retryable

Comprehensive retry decorator with smart exception handling for network operations, AWS services, and custom scenarios.

### Features
- **Automatic Retry**: Configurable retry attempts with exponential backoff
- **Smart Exception Handling**: Built-in support for common failure types
- **AWS Integration**: Specialized handling for boto3/botocore exceptions
- **Async Support**: Works with both sync and async functions
- **Detailed Logging**: Configurable verbosity for debugging

### Basic Usage

```python
from WrenchCL.Decorators import Retryable

@Retryable(max_retries=3, delay=2)
def unreliable_api_call():
    response = requests.get("https://api.example.com/data")
    return response.json()

# Automatic retry on network failures
result = unreliable_api_call()
```

### Advanced Configuration

```python
@Retryable(
    max_retries=5,
    delay=1,
    retry_on_exceptions=(ConnectionError, TimeoutError),
    verbose=True
)
def custom_operation():
    # Your code here
    pass

# AWS operations with built-in boto3 exception handling
@Retryable(max_retries=3, delay=2, verbose=True)
def s3_operation():
    return s3_client.get_object(Bucket='my-bucket', Key='my-key')
```

### Exception Handling

The decorator automatically handles common exception types:

**Network Exceptions:**
- `requests.exceptions.HTTPError`
- `requests.exceptions.ConnectionError` 
- `requests.exceptions.Timeout`
- `requests.exceptions.RequestException`

**AWS/Boto3 Exceptions:**
- `botocore.exceptions.ClientError`
- `botocore.exceptions.BotoCoreError`

**General Exceptions:**
- `json.JSONDecodeError`
- Custom exceptions via `retry_on_exceptions` parameter

### Async Support

```python
import asyncio

@Retryable(max_retries=3, delay=1)
async def async_api_call():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.example.com') as response:
            return await response.json()

# Usage
result = await async_api_call()
```

### HTTP Status Code Handling

```python
@Retryable(max_retries=3, delay=2)
def api_with_status_check():
    response = requests.get("https://api.example.com/data")
    # Automatically retries on non-200 status codes
    response.raise_for_status()  # Will retry on 4xx/5xx errors
    return response.json()
```

### Real-World Examples

#### Database Operations
```python
@Retryable(max_retries=3, delay=5, verbose=True)
def connect_to_database():
    return psycopg2.connect(
        host="db.example.com",
        database="myapp",
        user="user",
        password="password"
    )

# Automatically retries on connection failures
db_conn = connect_to_database()
```

#### S3 Operations
```python
@Retryable(max_retries=5, delay=2)
def upload_to_s3(file_data, bucket, key):
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_data
    )
    return f"s3://{bucket}/{key}"

# Handles temporary S3 throttling automatically
result = upload_to_s3(data, "my-bucket", "uploads/file.txt")
```

#### API Integration
```python
@Retryable(
    max_retries=4, 
    delay=3,
    retry_on_exceptions=(requests.exceptions.RequestException, ValueError),
    verbose=True
)
def fetch_user_data(user_id):
    response = requests.get(f"https://api.service.com/users/{user_id}")
    
    if response.status_code == 404:
        raise ValueError("User not found")  # Won't retry
    
    response.raise_for_status()  # Will retry on other HTTP errors
    return response.json()
```

---

## SingletonClass

Thread-safe singleton pattern enforcement that prevents multiple instances while maintaining clean class design.

### Features
- **Thread Safety**: Uses proper locking to prevent race conditions
- **Clean Design**: No manual `__new__` implementation required
- **Initialization Safety**: Prevents multiple initialization calls
- **Type Preservation**: Maintains original class name and documentation

### Basic Usage

```python
from WrenchCL.Decorators import SingletonClass

@SingletonClass
class DatabaseManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connections = {}
    
    def get_connection(self, database):
        if database not in self.connections:
            self.connections[database] = create_connection(
                self.connection_string, database
            )
        return self.connections[database]

# Multiple instantiations return the same object
db1 = DatabaseManager("postgresql://localhost/")
db2 = DatabaseManager("different_string")  # Same instance as db1

assert db1 is db2  # True
```

### Configuration Management

```python
@SingletonClass
class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        # Only called once, even with multiple instantiations
        self.config = {
            "database_url": os.getenv("DATABASE_URL"),
            "api_key": os.getenv("API_KEY"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)

# Safe to call from anywhere in the application
config = ConfigManager()
db_url = config.get("database_url")
```

### Logger Implementation

```python
@SingletonClass
class ApplicationLogger:
    def __init__(self):
        self.logger = logging.getLogger("app")
        self.setup_handlers()
    
    def setup_handlers(self):
        # Only setup once
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message, exc_info=None):
        self.logger.error(message, exc_info=exc_info)

# Consistent logger across the application
logger = ApplicationLogger()
logger.info("Application started")
```

### Error Prevention

```python
# This will raise a SingletonViolationException
@SingletonClass
class BadSingleton:
    def __new__(cls):  # ❌ Cannot override __new__ with @SingletonClass
        return super().__new__(cls)
    
    def __init__(self):
        pass

# Correct implementation
@SingletonClass  
class GoodSingleton:
    def __init__(self):  # ✅ Only override __init__
        self.initialized = True
```

---

## Synchronized

Method-level thread synchronization for safe concurrent access to shared resources.

### Features
- **Method Protection**: Ensures only one thread executes a method at a time
- **Flexible Locking**: Use custom locks for different synchronization strategies
- **Deadlock Prevention**: Proper lock management with context managers
- **Performance**: Minimal overhead when locks are not contended

### Basic Usage

```python
import threading
from WrenchCL.Decorators import Synchronized

class SharedCounter:
    def __init__(self):
        self.count = 0
        self._lock = threading.Lock()
    
    @Synchronized(_lock)
    def increment(self):
        # Thread-safe increment
        current = self.count
        time.sleep(0.001)  # Simulate processing
        self.count = current + 1
    
    @Synchronized(_lock)
    def get_count(self):
        return self.count

# Safe for concurrent access
counter = SharedCounter()

def worker():
    for _ in range(100):
        counter.increment()

# Run multiple threads
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter.get_count())  # Always 1000, never a race condition
```

### Database Connection Pool

```python
import threading
from queue import Queue

class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.created_connections = 0
        self._lock = threading.RLock()  # Reentrant lock
        
        # Pre-populate pool
        for _ in range(max_connections):
            self.pool.put(self._create_connection())
    
    def _create_connection(self):
        # Simulate connection creation
        self.created_connections += 1
        return f"connection_{self.created_connections}"
    
    @Synchronized(_lock)
    def get_connection(self):
        if self.pool.empty() and self.created_connections < self.max_connections:
            return self._create_connection()
        return self.pool.get()
    
    @Synchronized(_lock)
    def return_connection(self, connection):
        if not self.pool.full():
            self.pool.put(connection)
    
    @Synchronized(_lock)  
    def get_stats(self):
        return {
            "total_created": self.created_connections,
            "available": self.pool.qsize(),
            "max_size": self.max_connections
        }
```

### Cache Implementation

```python
import threading
import time
from typing import Any, Optional

class ThreadSafeCache:
    def __init__(self, ttl_seconds=300):
        self.cache = {}
        self.ttl = ttl_seconds
        self._lock = threading.RWLock()  # Reader-writer lock simulation
        
    @Synchronized(_lock)
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    @Synchronized(_lock)
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, time.time())
    
    @Synchronized(_lock)
    def clear_expired(self) -> int:
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        return len(expired_keys)
```

### Different Lock Types

```python
import threading

class MultiLockExample:
    def __init__(self):
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.data = {}
    
    @Synchronized(read_lock)
    def read_data(self, key):
        return self.data.get(key)
    
    @Synchronized(write_lock)
    def write_data(self, key, value):
        self.data[key] = value
    
    @Synchronized(write_lock)  # Use write lock for modifications
    def delete_data(self, key):
        if key in self.data:
            del self.data[key]
```

---

## Deprecated

Clean deprecation warnings with automatic tracking to prevent warning spam.

### Features
- **Automatic Tracking**: Warns only once per deprecated function
- **Custom Messages**: Provide context about alternatives
- **Stack Level Control**: Proper warning attribution
- **Module Tracking**: Tracks by module and function name

### Basic Usage

```python
from WrenchCL.Decorators import Deprecated

@Deprecated("Use new_function() instead")
def old_function(x, y):
    """This function will be removed in v2.0"""
    return x + y

@Deprecated()  # Default message
def legacy_method():
    pass

# First call shows warning, subsequent calls are silent
result = old_function(1, 2)  # ⚠️ DeprecationWarning: old_function is deprecated Use new_function() instead
result = old_function(3, 4)  # No warning (already shown)
```

### Migration Patterns

```python
# Gradual migration pattern
@Deprecated("Use process_data_v2() which supports async operations")
def process_data(data):
    """Legacy sync data processing"""
    return _legacy_processor(data)

def process_data_v2(data):
    """New async data processing"""
    return _new_async_processor(data)

# Method deprecation in classes
class APIClient:
    @Deprecated("Use fetch_user_profile() instead")
    def get_user(self, user_id):
        return self.fetch_user_profile(user_id)
    
    def fetch_user_profile(self, user_id):
        # New implementation
        pass
```

### Version-Specific Deprecation

```python
@Deprecated("Will be removed in v3.0. Use calculate_metrics() instead.")
def compute_stats(data):
    """Deprecated statistical computation"""
    return calculate_metrics(data)

@Deprecated("Replaced by async variant in v2.1. Use async_fetch() instead.")
def sync_fetch(url):
    """Synchronous fetch - deprecated"""
    return requests.get(url)
```

### Library Migration Example

```python
# When migrating from old library patterns
class DatabaseManager:
    @Deprecated("Use get_connection() instead")
    def connect(self):
        """Legacy connection method"""
        return self.get_connection()
    
    @Deprecated("Use execute_query() instead") 
    def run_sql(self, query):
        """Legacy SQL execution"""
        return self.execute_query(query)
    
    def get_connection(self):
        """New connection method"""
        pass
    
    def execute_query(self, query):
        """New query execution"""
        pass
```

---

## Advanced Patterns

### Combining Decorators

```python
import threading

@SingletonClass
class RetryableService:
    def __init__(self):
        self.lock = threading.Lock()
        self.call_count = 0
    
    @Synchronized(lock)
    @Retryable(max_retries=3, delay=1)
    def critical_operation(self):
        self.call_count += 1
        # Simulated operation that might fail
        if self.call_count < 3:
            raise ConnectionError("Temporary failure")
        return "Success"

# Thread-safe, retryable, singleton service
service = RetryableService()
result = service.critical_operation()
```

### Decorator Factory Pattern

```python
def smart_retry(operation_type="general"):
    """Factory for operation-specific retry configurations"""
    
    configs = {
        "database": {"max_retries": 5, "delay": 3, "verbose": True},
        "api": {"max_retries": 3, "delay": 1, "verbose": False},
        "file_io": {"max_retries": 2, "delay": 0.5, "verbose": True}
    }
    
    config = configs.get(operation_type, configs["general"])
    return Retryable(**config)

@smart_retry("database")
def database_operation():
    # Uses database-specific retry configuration
    pass

@smart_retry("api")
def api_call():
    # Uses API-specific retry configuration  
    pass
```

### Performance Monitoring Decorator

```python
import time
import threading
from functools import wraps

class PerformanceTracker:
    def __init__(self):
        self.stats = {}
        self.lock = threading.Lock()
    
    @Synchronized(lock)
    def record_call(self, func_name, duration):
        if func_name not in self.stats:
            self.stats[func_name] = {"calls": 0, "total_time": 0}
        
        self.stats[func_name]["calls"] += 1
        self.stats[func_name]["total_time"] += duration
    
    @Synchronized(lock)
    def get_stats(self):
        result = {}
        for func_name, data in self.stats.items():
            result[func_name] = {
                "calls": data["calls"],
                "avg_time": data["total_time"] / data["calls"],
                "total_time": data["total_time"]
            }
        return result

# Global tracker
tracker = PerformanceTracker()

def track_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            tracker.record_call(func.__name__, duration)
    return wrapper

# Usage
@track_performance
@Retryable(max_retries=2)
def monitored_operation():
    time.sleep(0.1)  # Simulate work
    return "completed"
```

---

## Best Practices

### Error Handling with Retryable
```python
# Be specific about which exceptions to retry
@Retryable(
    max_retries=3,
    retry_on_exceptions=(ConnectionError, TimeoutError),  # Don't retry on ValueError
    verbose=True
)
def specific_retry_operation():
    pass

# Use appropriate delays for different services
@Retryable(max_retries=5, delay=0.1)  # Fast retry for local operations
def local_cache_operation():
    pass

@Retryable(max_retries=3, delay=5)    # Slower retry for external APIs
def external_api_call():
    pass
```

### Thread Safety Considerations
```python
# Use appropriate lock types
class DataManager:
    def __init__(self):
        self.rw_lock = threading.RLock()  # Reentrant for complex operations
        self.simple_lock = threading.Lock()  # Simple lock for atomic operations
        
    @Synchronized(rw_lock)
    def complex_update(self):
        # Can call other synchronized methods safely
        self.simple_increment()
        
    @Synchronized(simple_lock) 
    def simple_increment(self):
        pass
```

### Singleton Best Practices
```python
# Initialize expensive resources once
@SingletonClass
class ResourceManager:
    def __init__(self):
        self.db_pool = self._create_database_pool()
        self.cache = self._initialize_cache()
        self.logger = self._setup_logging()
    
    def _create_database_pool(self):
        # Expensive operation done only once
        pass
```

The Decorators module provides robust, production-ready patterns that can be combined to create sophisticated, thread-safe, and resilient applications with clean separation of concerns.