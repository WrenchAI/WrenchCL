<h1 align="center">Wrench Code Library</h1>

<p align="center">
  <a href="https://pypi.org/project/wrench-code-library/"><img src="https://badge.fury.io/py/wrench-code-library.svg" alt="PyPI version" height="20"/></a>
  <img src="https://img.shields.io/badge/python-3.x-blue" alt="Python Version" height="20"/>
  <img src="https://img.shields.io/badge/repo-private-red" alt="Private Repo" height="20"/>
  <a href="https://github.com/Kydoimos97"><img src="https://img.shields.io/badge/maintainer-Kydoimos97-yellow" alt="Maintainer" height="20"/></a>
  <br>
  <a href="https://github.com/WrenchAI/wrench-code-library/stargazers"><img src="https://img.shields.io/github/stars/WrenchAI/wrench-code-library.svg" alt="GitHub Stars" height="20"/></a>
  <a href="https://github.com/WrenchAI/wrench-code-library/network/members"><img src="https://img.shields.io/github/forks/WrenchAI/wrench-code-library.svg" alt="GitHub Forks" height="20"/></a>
  <a href="https://github.com/WrenchAI/wrench-code-library/issues"><img src="https://img.shields.io/github/issues/WrenchAI/wrench-code-library.svg" alt="GitHub Issues" height="20"/></a>
  <a href="https://github.com/WrenchAI/wrench-code-library/pulls"><img src="https://img.shields.io/github/issues-pr/WrenchAI/wrench-code-library.svg" alt="GitHub Pull Requests" height="20"/></a>

  
</p>

## Description

This is a code library designed to improve code reusability and standardize access to APIs, RDS, and logging functionalities.

**Pypi Link: [https://pypi.org/project/wrench-code-library/](https://pypi.org/project/wrench-code-library/)**

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
