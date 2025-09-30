# Decorators

WrenchCL provides utility decorators for common patterns including retry logic, singleton implementation, and thread synchronization.

## Import Structure

```python
from WrenchCL.Decorators import Retryable, SingletonClass, Synchronized, Deprecated
```

## Retryable

Automatic retry logic with configurable parameters:

```python
from WrenchCL.Decorators import Retryable

# Basic usage (2 retries, 2-second delay)
@Retryable()
def unreliable_api_call():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# Custom configuration
@Retryable(max_retries=5, delay=1, verbose=True)
def database_operation():
    return perform_db_query()

# Specific exceptions only
@Retryable(
    max_retries=3,
    retry_on_exceptions=(ConnectionError, TimeoutError),
    delay=0.5
)
def network_operation():
    return fetch_data()
```

### Async Support

Works with both sync and async functions:

```python
@Retryable(max_retries=3, delay=1)
async def async_operation():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as response:
            response.raise_for_status()
            return await response.json()

# Usage
result = await async_operation()
```

## SingletonClass

Thread-safe singleton pattern:

```python
from WrenchCL.Decorators import SingletonClass

@SingletonClass
class LoggerStateManager:
    def __init__(self):
        self.config = {}
        self.loaded = False
    
    def load_config(self):
        if not self.loaded:
            self.config = load_from_file()
            self.loaded = True

# Multiple instantiations return same object
config1 = LoggerStateManager()
config2 = LoggerStateManager()
assert config1 is config2  # True

# Initialization only happens once
config1.load_config()
print(config2.loaded)  # True
```

### Restrictions

The decorator prevents certain patterns that would break singleton behavior:

```python
# This will raise SingletonViolationException
@SingletonClass
class InvalidSingleton:
    def __new__(cls):  # Not allowed
        return super().__new__(cls)
```

## Synchronized

Method-level thread synchronization:

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
        time.sleep(0.001)  # Simulate processing
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

# Thread-safe operations
account = BankAccount(1000)

def worker(account, operations):
    for op, amount in operations:
        if op == "deposit":
            account.deposit(amount)
        elif op == "withdraw":
            account.withdraw(amount)

# Safe concurrent access
threads = []
for i in range(10):
    ops = [("deposit", 10), ("withdraw", 5)] * 5
    t = threading.Thread(target=worker, args=(account, ops))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"Final balance: {account.get_balance()}")  # Predictable result
```

## Deprecated

Deprecation warnings with tracking:

```python
from WrenchCL.Decorators import Deprecated

@Deprecated("Use new_function() instead")
def old_function(data):
    return process_data_old_way(data)

@Deprecated()  # Default message
def legacy_method():
    pass

# Usage shows warning once per function
old_function(data)  # Warning: old_function is deprecated. Use new_function() instead
old_function(data)  # No warning (already shown)
legacy_method()     # Warning: legacy_method is deprecated...
```

## Combining Decorators

Decorators can be combined effectively:

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

### Decorator Order

Order matters when combining decorators:

```python
# Retry wraps synchronization (recommended)
@Retryable(max_retries=3)
@Synchronized(lock)
def operation():
    # Each retry attempt is synchronized
    pass

# Synchronization wraps retry (lock held across all attempts)
@Synchronized(lock) 
@Retryable(max_retries=3)
def operation():
    # Lock held for entire retry sequence
    pass
```

## Real-World Examples

### API Client

```python
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

client = APIClient()
data = client.get("users/123")
```

### Thread-Safe Cache

```python
@SingletonClass
class Cache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.RLock()
    
    @Synchronized(_lock)
    def get(self, key):
        return self._cache.get(key)
    
    @Synchronized(_lock)
    def set(self, key, value):
        self._cache[key] = value
    
    @Synchronized(_lock)
    def clear(self):
        self._cache.clear()

cache = Cache()
cache.set("key", "value")
```

### Migration Helper

```python
class DatabaseMigrator:
    @Deprecated("Use migrate_with_progress() for better feedback")
    def migrate(self, version):
        return self._old_migration_logic(version)
    
    def migrate_with_progress(self, version, callback=None):
        for step in self._get_migration_steps(version):
            self._execute_step(step)
            if callback:
                callback(step)

# Old code still works but shows warnings
migrator = DatabaseMigrator()
migrator.migrate("v2.0")  # Shows deprecation warning

# New code uses improved API
def progress_callback(step):
    print(f"Completed: {step.description}")

migrator.migrate_with_progress("v2.0", progress_callback)
```

All decorators are thread-safe and handle edge cases properly. They integrate well with WrenchCL's logging system for error reporting and debugging.