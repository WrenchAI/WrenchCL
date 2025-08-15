# Decorators

WrenchCL provides a collection of utility decorators for common patterns including retry logic, singleton implementation, synchronization, and deprecation warnings.

## Overview

The decorators module includes:

- **Retryable** - Automatic retry logic with exponential backoff
- **SingletonClass** - Thread-safe singleton pattern implementation
- **Synchronized** - Method-level thread synchronization
- **Deprecated** - Deprecation warnings with tracking

## Retryable Decorator

::: WrenchCL.Decorators.Retryable
    options:
      show_source: false
      heading_level: 3

### Basic Usage

```python
from WrenchCL.Decorators import Retryable

@Retryable()
def unreliable_api_call():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# Will retry up to 2 times with 2-second delays on failure
result = unreliable_api_call()
```

### Custom Configuration

```python
@Retryable(max_retries=5, delay=1, verbose=True)
def database_operation():
    # Operation that might fail
    return perform_db_query()

# Retry specific exceptions only
@Retryable(
    max_retries=3,
    retry_on_exceptions=(ConnectionError, TimeoutError),
    delay=0.5
)
def network_operation():
    return fetch_data_from_network()
```

### Async Support

```python
import asyncio

@Retryable(max_retries=3, delay=1)
async def async_operation():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as response:
            if response.status != 200:
                response.raise_for_status()
            return await response.json()

# Works with asyncio
result = await async_operation()
```

### Advanced Examples

```python
# Retry with exponential backoff (manual implementation)
import time
import random

@Retryable(max_retries=5, delay=0)
def custom_backoff_operation():
    try:
        return risky_operation()
    except Exception as e:
        # Custom backoff logic
        wait_time = (2 ** attempt) + random.uniform(0, 1)
        time.sleep(wait_time)
        raise

# Conditional retry based on exception
@Retryable(max_retries=3, verbose=True)
def selective_retry():
    try:
        return external_service_call()
    except RateLimitError:
        # Always retry rate limits
        raise
    except AuthenticationError:
        # Never retry auth errors
        return None
    except Exception:
        # Retry other exceptions
        raise
```

## SingletonClass Decorator

::: WrenchCL.Decorators.SingletonClass
    options:
      show_source: false
      heading_level: 3

### Basic Usage

```python
from WrenchCL.Decorators import SingletonClass

@SingletonClass
class ConfigManager:
    def __init__(self):
        self.config = {}
        self.loaded = False
    
    def load_config(self):
        if not self.loaded:
            # Expensive configuration loading
            self.config = load_from_file()
            self.loaded = True

# Multiple instantiations return the same object
config1 = ConfigManager()
config2 = ConfigManager()
assert config1 is config2  # True

# Initialization only happens once
config1.load_config()
print(config2.loaded)  # True
```

### Thread Safety

```python
import threading

@SingletonClass  
class DatabasePool:
    def __init__(self):
        self.connections = []
        self.lock = threading.RLock()
        print("DatabasePool initialized")
    
    def get_connection(self):
        with self.lock:
            # Thread-safe connection management
            return self.connections.pop() if self.connections else create_new_connection()

# Safe concurrent access
def worker():
    pool = DatabasePool()  # Same instance across all threads
    conn = pool.get_connection()
    # Use connection

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

### Common Patterns

```python
@SingletonClass
class Logger:
    def __init__(self, level="INFO"):
        self.level = level
        self.handlers = []
        
    def log(self, message):
        print(f"[{self.level}] {message}")

@SingletonClass
class Cache:
    def __init__(self):
        self._cache = {}
        
    def get(self, key):
        return self._cache.get(key)
    
    def set(self, key, value):
        self._cache[key] = value

# Global access pattern
def get_logger():
    return Logger()

def get_cache():
    return Cache()
```

### Restrictions

The decorator enforces certain restrictions to maintain singleton integrity:

```python
# This will raise SingletonViolationException
@SingletonClass
class InvalidSingleton:
    def __new__(cls):  # Not allowed
        return super().__new__(cls)
    
    def __init__(self):
        pass

# Correct implementation
@SingletonClass
class ValidSingleton:
    def __init__(self):
        self.data = {}
```

## Synchronized Decorator

::: WrenchCL.Decorators.Synchronized
    options:
      show_source: false
      heading_level: 3

### Basic Usage

```python
import threading
from WrenchCL.Decorators import Synchronized

class BankAccount:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self._lock = threading.RLock()
    
    @Synchronized(_lock)
    def deposit(self, amount):
        current = self.balance
        # Simulated processing time
        time.sleep(0.001)
        self.balance = current + amount
        return self.balance
    
    @Synchronized(_lock)
    def withdraw(self, amount):
        if self.balance >= amount:
            current = self.balance
            time.sleep(0.001)
            self.balance = current - amount
            return True
        return False
    
    @Synchronized(_lock)
    def get_balance(self):
        return self.balance

# Thread-safe operations
account = BankAccount(1000)

def worker(account, operations):
    for op, amount in operations:
        if op == "deposit":
            account.deposit(amount)
        elif op == "withdraw":
            account.withdraw(amount)

# Concurrent operations are safely synchronized
threads = []
for i in range(10):
    ops = [("deposit", 10), ("withdraw", 5)] * 10
    t = threading.Thread(target=worker, args=(account, ops))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"Final balance: {account.get_balance()}")  # Predictable result
```

### Class-Level Synchronization

```python
class SharedResource:
    _class_lock = threading.RLock()
    _instance_data = {}
    
    def __init__(self, resource_id):
        self.resource_id = resource_id
        self._instance_lock = threading.RLock()
    
    @Synchronized(_class_lock)
    @classmethod
    def create_resource(cls, resource_id):
        if resource_id not in cls._instance_data:
            cls._instance_data[resource_id] = cls(resource_id)
        return cls._instance_data[resource_id]
    
    @Synchronized(_instance_lock)
    def update_data(self, data):
        # Instance-level synchronization
        self.data = data
    
    @Synchronized(_class_lock)
    def cleanup_all(self):
        # Class-level synchronization
        self._instance_data.clear()
```

### Performance Considerations

```python
class OptimizedCounter:
    def __init__(self):
        self._value = 0
        self._read_lock = threading.RLock()
        self._write_lock = threading.RLock()
    
    # Separate locks for read and write operations
    @Synchronized(_read_lock)
    def get_value(self):
        return self._value
    
    @Synchronized(_write_lock)  
    def increment(self):
        with self._read_lock:  # Also acquire read lock
            self._value += 1
    
    @Synchronized(_write_lock)
    def decrement(self):
        with self._read_lock:
            self._value -= 1
```

## Deprecated Decorator

::: WrenchCL.Decorators.Deprecated
    options:
      show_source: false
      heading_level: 3

### Basic Usage

```python
from WrenchCL.Decorators import Deprecated

@Deprecated("Use new_function() instead")
def old_function(data):
    return process_data_old_way(data)

def new_function(data):
    return process_data_new_way(data)

# Using deprecated function shows warning
result = old_function(data)
# Warning: old_function is deprecated. Use new_function() instead
```

### Method Deprecation

```python
class DataProcessor:
    def __init__(self):
        pass
    
    @Deprecated("Use process_batch() for better performance")
    def process_single(self, item):
        return self._legacy_process(item)
    
    def process_batch(self, items):
        return [self._new_process(item) for item in items]
    
    @Deprecated()  # Default message
    def old_method(self):
        pass

processor = DataProcessor()
processor.old_method()  # Shows deprecation warning
```

### Tracking Deprecation Usage

```python
# The decorator tracks which deprecated functions are called
from WrenchCL.Decorators import Deprecated

@Deprecated("Replaced by v2 API")
def api_v1_method():
    pass

@Deprecated("No longer supported")
def legacy_feature():
    pass

# Call deprecated functions
api_v1_method()
legacy_feature()
api_v1_method()  # Only warns once per function

# Access tracking information
print(Deprecated.__depr_tracker__)
# {'__main__.api_v1_method', '__main__.legacy_feature'}
```

## Combining Decorators

Decorators can be combined for powerful functionality:

```python
import threading
from WrenchCL.Decorators import Retryable, Synchronized, SingletonClass

@SingletonClass
class DatabaseManager:
    def __init__(self):
        self._connection = None
        self._lock = threading.RLock()
    
    @Synchronized(_lock)
    @Retryable(max_retries=3, delay=1)
    def connect(self):
        if not self._connection:
            self._connection = create_database_connection()
        return self._connection
    
    @Synchronized(_lock)
    @Retryable(max_retries=2, delay=0.5)
    def execute_query(self, query, params=None):
        conn = self.connect()
        return conn.execute(query, params or [])

# Thread-safe, auto-retrying, singleton database manager
db = DatabaseManager()
result = db.execute_query("SELECT * FROM users")
```

### Order of Decorators

The order of decorators matters:

```python
# Correct order: Outer to inner execution
@Retryable(max_retries=3)
@Synchronized(lock)
def operation():
    # Synchronized operation that retries on failure
    pass

# This means:
# 1. Retry logic wraps everything
# 2. Each retry attempt is synchronized
# 3. Lock is held only during actual execution

# Alternative order:
@Synchronized(lock)
@Retryable(max_retries=3)
def operation():
    # Lock held across all retry attempts
    pass
```

## Real-World Examples

### Web Service Client

```python
import requests
from WrenchCL.Decorators import Retryable, SingletonClass

@SingletonClass
class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.example.com"
    
    @Retryable(max_retries=3, delay=1)
    def get(self, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    @Retryable(max_retries=2, delay=0.5)
    def post(self, endpoint, data=None, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data, **kwargs)
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient()
user_data = client.get("users/123")
result = client.post("users", data={"name": "John"})
```

### Cache Implementation

```python
import threading
import time
from WrenchCL.Decorators import SingletonClass, Synchronized

@SingletonClass
class TTLCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.RLock()
        self.default_ttl = 300  # 5 minutes
    
    @Synchronized(_lock)
    def get(self, key):
        if key in self._cache:
            if time.time() - self._timestamps[key] < self.default_ttl:
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    @Synchronized(_lock)
    def set(self, key, value, ttl=None):
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    @Synchronized(_lock)
    def clear_expired(self):
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp >= self.default_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
            del self._timestamps[key]

# Usage
cache = TTLCache()
cache.set("user:123", {"name": "John", "email": "john@example.com"})
user = cache.get("user:123")  # Returns data if not expired
```

### Migration Helper

```python
from WrenchCL.Decorators import Deprecated

class DatabaseMigrator:
    @Deprecated("Use migrate_with_progress() for better feedback")
    def migrate(self, version):
        return self._old_migration_logic(version)
    
    def migrate_with_progress(self, version, callback=None):
        # New implementation with progress tracking
        for step in self._get_migration_steps(version):
            self._execute_step(step)
            if callback:
                callback(step)
    
    @Deprecated()
    def rollback_all(self):
        # Dangerous operation
        pass

# Gradual migration from old to new API
migrator = DatabaseMigrator()

# Old code still works but shows warnings
migrator.migrate("v2.0")

# New code uses improved API
def progress_callback(step):
    print(f"Completed: {step.description}")

migrator.migrate_with_progress("v2.0", progress_callback)
```

## Best Practices

### Error Handling with Retryable

```python
@Retryable(max_retries=3, verbose=True)
def robust_operation():
    try:
        return perform_operation()
    except TemporaryError:
        # Let retryable handle this
        raise
    except PermanentError:
        # Don't retry permanent errors
        return None
    except Exception as e:
        # Log and decide whether to retry
        logger.warning(f"Unexpected error: {e}")
        raise
```

### Singleton Resource Management

```python
@SingletonClass
class ResourceManager:
    def __init__(self):
        self._resources = {}
        self._cleanup_registered = False
    
    def __del__(self):
        self.cleanup()
    
    def get_resource(self, name):
        if name not in self._resources:
            self._resources[name] = create_resource(name)
            if not self._cleanup_registered:
                atexit.register(self.cleanup)
                self._cleanup_registered = True
        return self._resources[name]
    
    def cleanup(self):
        for resource in self._resources.values():
            resource.close()
        self._resources.clear()
```

### Thread Safety Guidelines

```python
class ThreadSafeProcessor:
    def __init__(self):
        self._data = {}
        self._lock = threading.RLock()  # Reentrant lock
    
    @Synchronized(_lock)
    def process_item(self, item):
        # Can safely call other synchronized methods
        if self._should_cache(item):
            self._cache_item(item)
        return self._transform_item(item)
    
    @Synchronized(_lock)
    def _cache_item(self, item):
        self._data[item.id] = item
    
    @Synchronized(_lock)  
    def _should_cache(self, item):
        return item.id not in self._data
    
    def _transform_item(self, item):
        # No synchronization needed for pure functions
        return item.upper()
```