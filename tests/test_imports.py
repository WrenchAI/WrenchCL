import atexit

import pytest

pytestmark = pytest.mark.skipif(False, reason="datadog_itr_unskippable")


def test_internal_import():
    try:
        import WrenchCL._Internal
    except ImportError as e:
        pytest.fail(f"Importing WrenchCL._Internal failed: {e}")


def test_connect_import():
    try:
        from WrenchCL.Connect import S3ServiceGateway, RdsServiceGateway, AwsClientHub
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Connect failed: {e}")


def test_decorators_import():
    try:
        from WrenchCL.Decorators import Retryable, SingletonClass
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Decorators failed: {e}")


def test_tools_import():
    try:
        from WrenchCL.Tools import (
            coalesce,
            get_file_type,
            image_to_base64,
            Maybe,
            get_metadata,
            robust_serializer,
            validate_base64,
            single_quote_decoder
            )
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Tools failed: {e}")


def test_logger_import():
    try:
        from WrenchCL import logger
    except ImportError as e:
        pytest.fail(f"Importing logger from WrenchCL failed: {e}")


@atexit.register
def shutdown_logging():
    import logging
    logging.shutdown()


if __name__ == "__main__":
    pytest.main()
