import pytest

from WrenchCL import logger
from WrenchCL.Tools import parse_json, safe_json_loader, list_loader


@pytest.fixture
def examples():
    """
    Fixture to provide test examples with nested and complex JSON structures.
    """
    examples = {
        "valid_nested_json": {
            "Payload": '{"status": "ok", "details": "{\\"level1\\": \\"{\\\\\\"level2\\\\\\": \\\\\\"{\\\\\\\\\\\\\\"level3\\\\\\\\\\\\\\": \\\\\\\\\\\\\\"value\\\\\\\\\\\\\\"}\\\\\\"}\\"}"}',
            "Metadata": {
                "info": '{"timestamp": "2025-01-28T12:34:56Z", "history": "[{\\"action\\": \\"created\\", \\"time\\": \\"2025-01-28T11:00:00Z\\"}]"}'
            }
        },
        "json_with_list_of_mixed_types": {
            "Payload": '{"status": "success", "results": "[{\\"id\\": 1, \\"value\\": \\"{\\\\\\"nested\\\\\\": \\\\\\"{\\\\\\\\\\\\\\"key\\\\\\\\\\\\\\": 42}\\\\\\"}\\"}, \\"raw string\\"]"}',
            "Metadata": {
                "history": '[{"event": "start", "data": "simple"}, "non-json-string", {"event": "end", "data": "{\\"nested\\": \\"deep\\"}"}]'
            }
        },
        "malformed_json_in_payload": {
            "Payload": '{"data": "{\\"level1\\": \\"{\\\\\\"level2\\\\\\": \\\\\\"{\\\\\\\\\\\\\\"stream\\\\\\\\\\\\\\": \\\\\\\\\\\\\\"raw text\\\\\\\\\\\\\\"}\\\\\\"}\\"}"}',
            "Metadata": {
                "info": '{"timestamp": "2025-01-28T12:34:56Z", "details": "{\\"status\\": \\"malformed\\", \\"data\\": [{\\"key\\": 1}, \\"malformed-string\\"]}"}',
                "tags": ["simple", '{"complex": "{\\"key\\": \\"value\\"}"}']
            }
        },
        "json_with_list": {
            "Payload": '[{"id": 1, "data": "{\\"nested\\": \\"{\\\\\\"key\\\\\\": \\\\\\"value\\\\\\"}\\"}"}, {"id": 2, "data": "plain text"}]',
            "Metadata": '{"history": "[{\\"event\\": \\"start\\"}, {\\"event\\": \\"end\\", \\"data\\": \\"{\\\\\\"nested\\\\\\": \\\\\\"deep\\\\\\"}\\"}]"}'
        },
        "recursive_abort": {},  # Cyclic reference set below
        "malformed_escape": {
            "Payload": '{"level1": "{\\"level2\\": \\"{\\\\\\"level3\\\\\\": \\\\\\"{\\\\\\\\\\\"key\\\\\\\\\": \\\\\\\\\\\"{\\\\\\\\\\\\\\\\\\\\\\\\"malformed\\\\\\\\\\\\\\\\\\\\\\\\"}\\\\\\\\\\\\"}\\"}\\"}"}',
            "Metadata": {
                "data": [
                    '{"key": "value"}',
                    '{"malformed_json": "{\\"missing_end"}',
                    '{"nested_list": "[{\\"key\\": 1}, {\\"key\\": 2}]"}'
                ]
            }
        }
    }

    # Create a cyclic reference for Example 5
    example_5 = {}
    example_5["Payload"] = {"nested": None}  # Initialize as a dictionary
    example_5["Payload"]["nested"] = example_5["Payload"]
    examples["recursive_abort"] = example_5

    return examples

@pytest.mark.parametrize("example_name", [
    "valid_nested_json",
    "json_with_list_of_mixed_types",
    "malformed_json_in_payload",
    "json_with_list",
    "recursive_abort",
    "malformed_escape"
])
def test_parse_response(example_name, examples, caplog):
    """
    Test the parse_response function with various nested and complex examples.
    """
    example_data = examples[example_name]
    logger.setLevel("DEBUG")

    logger.info(f"Processing {example_name}")
    try:
        parsed = parse_json(example_data)
        logger.data(parsed)
        # Validate the parsed response based on the example
        if example_name == "valid_nested_json":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "Metadata" in parsed
            assert parsed["Payload"]["status"] == "ok"
            assert parsed["Payload"]["details"]["level1"]["level2"]["level3"] == "value"
            assert parsed["Metadata"]["info"]["timestamp"] == "2025-01-28T12:34:56Z"
            assert parsed["Metadata"]["info"]["history"][0]["action"] == "created"

        elif example_name == "json_with_list_of_mixed_types":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "Metadata" in parsed
            assert parsed["Payload"]["status"] == "success"
            assert parsed["Payload"]["results"][0]["id"] == 1
            assert parsed["Payload"]["results"][0]["value"]["nested"]["key"] == 42
            assert parsed["Metadata"]["history"][0]["event"] == "start"
            assert parsed["Metadata"]["history"][2]["data"]["nested"] == "deep"

        elif example_name == "malformed_json_in_payload":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "Metadata" in parsed
            assert parsed["Payload"]["data"]["level1"]["level2"]["stream"] == "raw text"
            assert parsed["Metadata"]["info"]["timestamp"] == "2025-01-28T12:34:56Z"
            assert parsed["Metadata"]["tags"][1]["complex"]["key"] == "value"

        elif example_name == "json_with_list":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "Metadata" in parsed
            assert parsed["Payload"][0]["id"] == 1
            assert parsed["Payload"][0]["data"]["nested"]["key"] == "value"
            assert parsed["Metadata"]["history"][1]["event"] == "end"
            assert parsed["Metadata"]["history"][1]["data"]["nested"] == "deep"

        elif example_name == "recursive_abort":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "nested" in parsed["Payload"]
            assert parsed["Payload"]["nested"] is parsed["Payload"]  # Cyclic reference check

        elif example_name == "malformed_escape":
            assert isinstance(parsed, dict)
            assert "Payload" in parsed
            assert "Metadata" in parsed
            assert isinstance(parsed["Payload"], str)
            assert parsed["Metadata"]["data"][0]["key"] == "value"
            assert parsed["Metadata"]["data"][1]["malformed_json"] == '{"missing_end'
            assert parsed["Metadata"]["data"][2]["nested_list"][0]["key"] == 1

        logger.data(parsed)
    except Exception as e:
        logger.error(f"Error processing {example_name}: {str(e)}")
        if example_name == "recursive_abort":
            assert "Maximum recursion depth" in str(e), f"{example_name} failed for the wrong reason."
        else:
            pytest.fail(f"Unexpected error in {example_name}: {str(e)}")


def test_safe_json_loader_valid_cases():
    """
    Test the safe_json_loader function with valid JSON inputs.
    """
    assert safe_json_loader('{"key": "value"}') == {"key": "value"}
    assert safe_json_loader('[{"key": 1}, {"key": 2}]') == [{"key": 1}, {"key": 2}]


def test_safe_json_loader_malformed_cases():
    """
    Test the safe_json_loader function with malformed JSON inputs.
    """
    assert safe_json_loader('{"key": "value"') == '{"key": "value"'
    assert safe_json_loader("not a json") == "not a json"


def test_list_loader_valid_and_malformed():
    """
    Test the list_loader function with mixed valid and malformed inputs.
    """
    test_list = [
        '{"key": 1}',
        '{"key": "malformed',
        "not a json",
        '{"nested": {"key": "value"}}'
    ]
    parsed = list_loader(test_list)
    assert parsed == [
        {"key": 1},
        '{"key": "malformed',
        "not a json",
        {"nested": {"key": "value"}}
    ]


def test_max_recursion_depth():
    """
    Test parse_json for maximum recursion depth handling.
    """
    nested_json = '{"key":' + '{"nested":' * 30 + '"value"' + "}" * 30 + "}"
    with pytest.raises(RecursionError):
        parse_json(nested_json, max_depth=25)


def test_large_json():
    """
    Test parse_json with a very large JSON structure.
    """
    large_json = {"key": [{"nested": i} for i in range(1000)]}
    parsed = parse_json(large_json)
    assert len(parsed["key"]) == 1000
    assert parsed["key"][0] == {"nested": 0}



if __name__ == "__main__":
    pytest.main()
