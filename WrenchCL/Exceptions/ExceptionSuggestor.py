#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import inspect
import re
from collections.abc import Mapping
from difflib import get_close_matches
from typing import Iterable, List, Optional, Union


class ExceptionSuggestor:
    """
    Suggestion utility for catching and suggesting fixes for common missing key/attribute errors.
    Supports Pandas, _MockPandas, dicts, CLI options, and generic objects.
    """

    @classmethod
    def suggest_similar(
        cls,
        missing_key: str,
        available_keys: Iterable[str],
        n_suggestions: int = 1,
        cutoff: float = 0.6,
        case_insensitive: bool = True,
        return_message: bool = True,
        custom_message: Optional[str] = None
    ) -> Union[str, List[str], None]:
        keys = list(map(str, available_keys))
        key = str(missing_key)

        if case_insensitive:
            key = key.lower()
            keys_lower = [k.lower() for k in keys]
            matches = get_close_matches(key, keys_lower, n=n_suggestions, cutoff=cutoff)
            matches_original_case = [keys[keys_lower.index(m)] for m in matches]
        else:
            matches_original_case = get_close_matches(key, keys, n=n_suggestions, cutoff=cutoff)

        if not matches_original_case:
            return None

        if return_message:
            msg_template = custom_message or "Did you mean: {}?"
            joined = ", ".join(f"'{m}'" for m in matches_original_case)
            return msg_template.format(joined)

        return matches_original_case

    @classmethod
    def suggest_for_pandas_column(cls, missing_column: str, dataframe_columns: Iterable[str]) -> Optional[str]:
        return cls.suggest_similar(
            missing_key=missing_column,
            available_keys=dataframe_columns,
            n_suggestions=1,
            cutoff=0.6,
            case_insensitive=True,
            return_message=True,
            custom_message="Column '{}' not found. Did you mean: {}?".format(missing_column, '{}')
        )

    @classmethod
    def suggest_for_dict_key(cls, missing_key: str, dict_keys: Iterable[str]) -> Optional[str]:
        return cls.suggest_similar(
            missing_key=missing_key,
            available_keys=dict_keys,
            n_suggestions=3,
            cutoff=0.7,
            case_insensitive=True,
            return_message=True,
            custom_message="Key '{}' not found. Possible matches: {}".format(missing_key, '{}')
        )

    @classmethod
    def suggest_for_cli_option(cls, invalid_option: str, valid_options: Iterable[str]) -> Optional[str]:
        return cls.suggest_similar(
            missing_key=invalid_option,
            available_keys=valid_options,
            n_suggestions=3,
            cutoff=0.5,
            case_insensitive=False,
            return_message=True,
            custom_message="Unrecognized option '{}'. Did you mean: {}?".format(invalid_option, '{}')
        )

    @classmethod
    def suggest_for_api_field(cls, missing_field: str, valid_fields: Iterable[str]) -> Optional[str]:
        return cls.suggest_similar(
            missing_key=missing_field,
            available_keys=valid_fields,
            n_suggestions=2,
            cutoff=0.65,
            case_insensitive=True,
            return_message=True,
            custom_message="Field '{}' not found. Closest matches: {}".format(missing_field, '{}')
        )

    @classmethod
    def _is_pandas_df(cls, obj):
        try:
            import pandas as pd
            if isinstance(obj, pd.DataFrame):
                return True
        except ImportError:
            pd = None
            pass

        try:
            from WrenchCL._Internal._MockPandas import _MockPandas  # Adjust import
            if isinstance(obj, _MockPandas.DataFrame):
                return True
        except ImportError:
            _MockPandas = None
            pass

        return False

    @classmethod
    def _suggest_for_exception(cls, error: BaseException, frame_depth=20, n_suggestions=1, cutoff=0.6) -> Optional[str]:
        if not isinstance(error, BaseException):
            return None
        error_msg = error.args[0]
        if not error.__class__.__name__.lower() in error_msg.lower():
            error_msg = f"  {error.__class__.__name__}: {error_msg}"
        else:
            error_msg = f"  {error_msg}"

        obj_match = re.search(r"'(\w+)' object has no attribute", error_msg)
        key_match = re.search(r"has no attribute '(\w+)'", error_msg)

        if not key_match:
            return error_msg

        source_obj = obj_match.group(1) if obj_match else None
        missing_attr = key_match.group(1)

        for frame in reversed(inspect.stack()[:frame_depth]):
            for var in frame.frame.f_locals.values():
                if not hasattr(var, '__class__'):
                    continue
                if var.__class__.__name__ == source_obj:
                    keys = [k for k in dir(var) if not k.startswith('__')]
                    matches = get_close_matches(missing_attr, keys, n=n_suggestions, cutoff=cutoff)
                    if matches:
                        return f"{error_msg}\n    Did you mean: {', '.join(matches)}?\n"
        return error_msg

    @classmethod
    def suggest(cls, obj: Union[BaseException, 'pandas.DataFrame', dict, tuple, set, list, object], missing_key: str = None) -> Optional[str]:
        """
        Auto-detect object type and route to appropriate suggestion method.
        """
        if missing_key is None and not isinstance(obj, BaseException):
            raise ValueError("Missing key must be provided when obj is not an Exception.")
        elif missing_key is None and isinstance(obj, BaseException):
            return cls._suggest_for_exception(obj)

        if cls._is_pandas_df(obj):
            return cls.suggest_for_pandas_column(missing_key, obj.columns)

        elif isinstance(obj, Mapping):
            return cls.suggest_for_dict_key(missing_key, obj.keys())

        elif isinstance(obj, (list, tuple, set)):
            return cls.suggest_for_cli_option(missing_key, obj)

        else:
            return cls.suggest_similar(
                missing_key=missing_key,
                available_keys=dir(obj),
                n_suggestions=2,
                cutoff=0.5,
                case_insensitive=True,
                return_message=True,
                custom_message="Attribute '{}' not found. Closest matches: {}".format(missing_key, '{}')
            )
