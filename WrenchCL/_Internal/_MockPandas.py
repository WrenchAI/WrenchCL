


#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

class _MockPandas:
    """A mock pandas class for environments where pandas is not installed."""

    class DataFrame:
        """Mock DataFrame that safely handles calls but performs no actual operations."""
        def __init__(self, *args, **kwargs):
            self.data = kwargs.get("data", {})
            self.columns = list(self.data.keys()) if isinstance(self.data, dict) else []

        def applymap(self, func):
            """Mock applymap function to safely handle DataFrame element-wise operations."""
            return self  # No-op for applymap

        def itertuples(self, index: bool = True, name: str = "Row"):
            """Mock itertuples function to iterate over rows as named tuples."""
            for row in zip(*self.data.values()):
                yield tuple(row)

    class Series:
        """Mock Series that safely handles calls but performs no actual operations."""
        def __init__(self, data=None, *args, **kwargs):
            self.data = data

        def apply(self, func):
            """Mock apply function to safely handle Series element-wise operations."""
            return self  # No-op for apply

    class api:
        """Mock pandas.api for checking data types."""
        class types:
            @staticmethod
            def is_object_dtype(column):
                """Check if a column is an object type (always returns False)."""
                return False  # Simplified mock behavior

            @staticmethod
            def is_datetime64_any_dtype(column):
                """Check if a column is a datetime type (always returns False)."""
                return False  # Simplified mock behavior

            @staticmethod
            def is_timedelta64_dtype(column):
                """Check if a column is a timedelta type (always returns False)."""
                return False  # Simplified mock behavior

    @staticmethod
    def isna(value):
        """Mock pandas.isna function to check for None or NaN."""
        return value is None or (isinstance(value, float) and value != value)  # Handles NaN

    @staticmethod
    def notnull(value):
        """Mock pandas.notnull function to check for not-None and not-NaN values."""
        return not _MockPandas.isna(value)

    def __init__(self):
        """Mock pandas.options."""
        self.options = {}

