<h1 align="center">Wrench Code Library</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.x-blue" alt="Python Version" height="20"/>
  <img src="https://img.shields.io/badge/repo-private-red" alt="Private Repo" height="20"/>
  <a href="https://github.com/Kydoimos97"><img src="https://img.shields.io/badge/maintainer-Kydoimos97-blue" alt="Maintainer" height="20"/></a>
</p>


## Description

This is a code library designed to improve code reusability and standardize access to APIs, RDS, and logging functionalities.

## Installation

To install the package, simply run:

```bash
pip install wrench-code-library
```

## Extending the ApiSuperClass

To use `ApiSuperClass` for your specific API, create a subclass that implements the following methods:

### Methods

- `get_count()`: Returns the total number of records meeting specific conditions.
- `fetch_data()`: Fetches data from the API in a specific format.

### Example

```python
from src.ApiSuperClass import ApiSuperClass

class YourApiSubClass(ApiSuperClass):
    def __init__(self, your_params):
        super().__init__('your_base_url')
        # Initialization code here

    def get_count(self):
        # Implementation here
        pass

    def fetch_data(self, batch_size=100, last_record_sort_value=None, last_record_unique_id=None, page=None):
        # Implementation here
        pass
```

## Extending the _RdsSuperClass

To use `_RdsSuperClass` for specific database operations, you don't need to create a subclass unless methods need to be overridden.

### Example

```python
from src.Components.RdsSuperClass import rdsInstance

# Regular Implementation
rdsInstance.connect()

# Overriding Methods
class YourDatabaseSubClass(_RdsSuperClass):
    def __init__(self, your_params):
        super().__init__('your_secrets_path')
        # Initialization code here

    # Override or extend existing methods as needed
```
```

### Notes

- The badges at the top are placeholders. Replace `yourusername` and `yourrepository` with your actual GitHub username and repository name.
- I've added section headers and clarified some of the text to make the document easier to read.

Remember to update the `long_description` in your `setup.py` to read from this improved README, and set `long_description_content_type` to `text/markdown`.
