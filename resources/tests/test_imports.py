#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

def test_all_imports():
    # Import from WrenchCL/_Internal
    try:
        import WrenchCL._Internal
    except ImportError as e:
        assert False, f"Importing WrenchCL._Internal failed: {e}"

    # Import from WrenchCL/Connect
    try:
        from WrenchCL.Connect import RdsServiceGateway, S3ServiceGateway, AwsClientHub
    except ImportError as e:
        assert False, f"Importing from WrenchCL.Connect failed: {e}"

    # Import from WrenchCL/DataFlow
    try:
        from WrenchCL.DataFlow import (
            build_return_json,
            handle_lambda_response,
            GuardedResponseTrigger,
            trigger_minimum_dataflow_metrics,
            trigger_dataflow_metrics
        )
    except ImportError as e:
        assert False, f"Importing from WrenchCL.DataFlow failed: {e}"

    # Import from WrenchCL/Decorators
    try:
        from WrenchCL.Decorators import Retryable, SingletonClass, TimedMethod
    except ImportError as e:
        assert False, f"Importing from WrenchCL.Decorators failed: {e}"

    # Import from WrenchCL/Models/OpenAI
    try:
        from WrenchCL.Models.OpenAI import OpenAIFactory, OpenAIGateway
    except ImportError as e:
        assert False, f"Importing from WrenchCL.Models.OpenAI failed: {e}"

    # Import from WrenchCL/Tools
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
        assert False, f"Importing from WrenchCL.Tools failed: {e}"

    # Import logger from WrenchCL
    try:
        from WrenchCL import logger
    except ImportError as e:
        assert False, f"Importing logger from WrenchCL failed: {e}"

    # If no import errors, the test passes
    assert True

if __name__ == "__main__":
    import pytest
    pytest.main()
