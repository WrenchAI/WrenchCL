# Wrench Project Template

## Extending the ApiSuperClass

To use `ApiSuperClass` for your specific API, you'll need to create a subclass that implements the following methods:

- `get_count()`: This method should return the total number of records that meet your specific conditions.
- `fetch_data()`: This method should fetch data from the API and return it in a specific format.

Here's a template to get you started:

```python
from src.ApiSuperClass import ApiSuperClass


class YourApiSubClass(ApiSuperClass):
    def __init__(self, your_params):
        super().__init__('your_base_url')
        # your initialization code here

    def get_count(self):
        # your implementation here
        pass

    def fetch_data(self, batch_size=100, last_record_sort_value=None, last_record_unique_id=None, page=None):
        # your implementation here
        pass
```

## Extending the _RdsSuperClass

To use `_RdsSuperClass` for your specific database operations.
You don't need to create a subclass if no methods have to be overwritten.

Here's a template to get you started:

```python
from src.Components.RdsSuperClass import rdsInstance

# Regular Implementation
rdsInstance.connect()

# Overwrite
class YourDatabaseSubClass(_RdsSuperClass):
    def __init__(self, your_params):
        super().__init__('your_secrets_path')
        # your initialization code here

    # Override or extend existing methods as needed
