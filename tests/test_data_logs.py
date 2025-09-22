import json
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import List, Optional

import pandas as pd
import pytest
import yaml
from pydantic import BaseModel

from WrenchCL import logger


class UserSchema(BaseModel):
    id: int
    name: str
    email: Optional[str]
    permissions: List[str]


@pytest.fixture(autouse=True)
def reset_logger_mode():
    # Force terminal mode by default for clean output
    with logger.temporary(mode='terminal', deployed=False):
        yield


def test_json_file_logging():
    data = {"name": "test", "value": [1, 2, 3], "nested": {"a": True, "b": None}}
    logger.attach_global_stream('INFO')
    logger.force_markup()
    with NamedTemporaryFile(mode='w+', suffix=".json") as f:
        json.dump(data, f)
        f.seek(0)
        loaded = json.load(f)
        logger.data(loaded, compact=False)
        logger.data(loaded, compact=True)
        logger.info(loaded)


def test_yaml_file_logging():
    data = {"env": "test", "params": {"lr": 0.01, "epochs": 10}}
    with NamedTemporaryFile(mode='w+', suffix=".yaml") as f:
        yaml.dump(data, f)
        f.seek(0)
        loaded = yaml.safe_load(f)
        logger.data(loaded)
        logger.info(loaded)


def test_csv_file_logging():
    df = pd.DataFrame({"id": [1, 2, 3], "score": [0.91, 0.85, 0.77]})
    with NamedTemporaryFile(mode='w+', suffix=".csv") as f:
        df.to_csv(f, index=False)
        f.seek(0)
        df_loaded = pd.read_csv(f)
        logger.data(df_loaded)


def test_txt_file_logging():
    content = "This is line 1\nThis is line 2\nFinal line."
    with NamedTemporaryFile(mode='w+', suffix=".txt") as f:
        f.write(content)
        f.seek(0)
        raw_text = f.read()
        logger.data(raw_text)


def test_logger_in_json_mode_for_dict():
    obj = {"user": "admin", "access": "granted", "features": ["x", "y", "z"]}
    with logger.temporary(mode='json', deployed=True):
        print(logger.state)
        logger.data(obj)
    with logger.temporary(mode='json', deployed=False):
        print(logger.state)
        logger.data(obj)


def test_logger_in_json_mode_for_dataframe():
    df = pd.DataFrame({"name": ["A", "B"], "value": [1, 2]})
    with logger.temporary(mode='json', deployed=True):
        logger.data(df)


def test_logger_with_pydantic_model():
    user = UserSchema(
            id=123,
            name="Willem",
            email="willem@wrench.ai",
            permissions=["admin", "editor"]
            )
    logger.data(user)


def test_logger_with_pydantic_model_json_mode():
    user = UserSchema(
            id=456,
            name="Ada",
            email=None,
            permissions=["viewer"]
            )
    with logger.temporary(mode='json', deployed=True):
        logger.data(user)
