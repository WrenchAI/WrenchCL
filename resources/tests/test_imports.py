import pytest

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

def test_dataflow_import():
    try:
        from WrenchCL.DataFlow import (
            build_return_json,
            handle_lambda_response,
            GuardedResponseTrigger,
            trigger_minimum_dataflow_metrics,
            trigger_dataflow_metrics
        )
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.DataFlow failed: {e}")

def test_decorators_import():
    try:
        from WrenchCL.Decorators import Retryable, SingletonClass, TimedMethod
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Decorators failed: {e}")

def test_models_openai_import():
    try:
        from WrenchCL.Models.OpenAI import OpenAIFactory, OpenAIGateway
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Models.OpenAI failed: {e}")

def test_tools_import():
    try:
        from WrenchCL.Tools import (
            coalesce,
            get_file_type,
            image_to_base64,
            Maybe,
            logger,
            validate_input_dict,
            get_metadata
        )
    except ImportError as e:
        pytest.fail(f"Importing from WrenchCL.Tools failed: {e}")

def test_logger_import():
    try:
        from WrenchCL import logger
    except ImportError as e:
        pytest.fail(f"Importing logger from WrenchCL failed: {e}")

if __name__ == "__main__":
    pytest.main()
