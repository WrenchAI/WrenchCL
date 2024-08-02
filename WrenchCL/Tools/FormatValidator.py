import json
import os
import uuid
from pathlib import Path
from typing import Union
from .WrenchLogger import Logger
logger = Logger()


class FormatValidator:
    """
    A class to validate the format of input dictionaries against a specified format.

    :param format_input: The format specification, either as a dictionary or a path to a JSON file.
    :type format_input: Union[dict, str, os.PathLike]
    :param input_dict: The input dictionary to be validated, either as a dictionary or a path to a JSON file.
    :type input_dict: Union[dict, str, os.PathLike]

    Example of format dictionary:

    .. code-block:: python

        FORMAT_DICT = {
            'dict': dict,
            'str': str,
            'list': list,
            'int': int,
            'float': float,
            'tuple': tuple,
            'optional': type(None),
            'None': type(None),
            None: type(None),
            'uuid': uuid.UUID,
        }
    """

    def __init__(self, format_input: Union[dict, str, os.PathLike], input_dict: Union[dict, str, os.PathLike]):
        self.format_dict = self._load_dict_or_json(format_input)
        self.input_dict = self._load_dict_or_json(input_dict)
        self.output_dict = {}
        self._validate_formats()
        logger.debug("Format checks passed")

    def get_output_dict(self) -> dict:
        """
        Get the validated output dictionary.

        :return: The validated output dictionary.
        :rtype: dict
        """
        return self.output_dict

    @classmethod
    def validate_format(cls, format_input: Union[dict, str, os.PathLike], input_dict: Union[dict, str, os.PathLike]) -> dict:
        """
        Validate the input dictionary against the provided format specification.

        :param format_input: The format specification, either as a dictionary or a path to a JSON file.
        :type format_input: Union[dict, str, os.PathLike]
        :param input_dict: The input dictionary to be validated, either as a dictionary or a path to a JSON file.
        :type input_dict: Union[dict, str, os.PathLike]
        :return: The validated output dictionary.
        :rtype: dict

        Example of format dictionary:

        .. code-block:: python

            FORMAT_DICT = {
                'dict': dict,
                'str': str,
                'list': list,
                'int': int,
                'float': float,
                'tuple': tuple,
                'optional': type(None),
                'None': type(None),
                None: type(None),
                'uuid': uuid.UUID,
            }
        """
        validator = cls(format_input, input_dict)
        return validator.get_output_dict()

    def _load_dict_or_json(self, obj: Union[dict, str, os.PathLike]) -> dict:
        """
        Load a dictionary from a JSON file if a path is provided, otherwise return the dictionary.

        :param obj: The dictionary or path to a JSON file.
        :type obj: Union[dict, str, os.PathLike]
        :return: The loaded dictionary.
        :rtype: dict
        :raises FileNotFoundError: If the JSON file path does not exist.
        """
        if isinstance(obj, dict):
            return obj

        format_path = obj if os.path.isabs(obj) else os.path.join(os.getcwd(), obj)

        if not os.path.exists(format_path):
            raise FileNotFoundError(f"Cannot find format json at location {format_path}")

        with open(format_path, 'r') as file:
            return json.load(file)

    def _validate_formats(self) -> None:
        """
        Validate the input dictionary against the format dictionary.

        :raises KeyError: If a key in the input dictionary is not in the format dictionary.
        :raises ValueError: If a value in the input dictionary does not match the expected format.
        """
        self.output_dict = {}
        for key, value in self.input_dict.items():
            if key not in self.format_dict:
                print(self.format_dict.keys())
                raise KeyError(f"Invalid key '{key}' in dictionary")
            else:
                try:
                    self.output_dict[key] = self._validate_value(value, self.format_dict[key], key)
                    logger.debug(f"Valid value '{value}' for key '{key}'")
                except ValueError as e:
                    logger.error(e)
                    raise e

    @staticmethod
    def _validate_value(value, expected_format, key):
        """
        Validate a value against an expected format.

        :param value: The value to be validated.
        :type value: any
        :param expected_format: The expected format, either a type or a list of acceptable values.
        :type expected_format: list or type
        :param key: The key associated with the value.
        :type key: str
        :return: The validated and potentially converted value.
        :rtype: any
        :raises ValueError: If the value does not match the expected format.
        """
        pass_flag = False
        if str(value).lower() in ['null', 'none', 'na', 'nan', '']:
            value = None
        if isinstance(expected_format, list):
            if 'str' in expected_format:
                expected_format.append(expected_format.pop(expected_format.index('str')))
            if set(expected_format).issubset(expected_format.keys()):
                for expected_type in expected_format:
                    logger.debug(f"Checking if {value} is type {expected_format[expected_type].__name__}")
                    try:
                        value_casted = expected_format[expected_type](value)
                    except (ValueError, TypeError):
                        value_casted = value
                    if isinstance(value_casted, expected_format[expected_type]):
                        logger.debug(f"{value_casted} is type {expected_format[expected_type].__name__}")
                        return value_casted
                if not pass_flag:
                    raise ValueError(f"Invalid value '{value}' for key '{key}'")
            elif value.lower() not in expected_format:
                raise ValueError(f"Invalid value '{value}' for key '{key}'")
            else:
                logger.debug(f"Valid value: '{value}' is found in {expected_format}'")
                return value.lower()
        return value
