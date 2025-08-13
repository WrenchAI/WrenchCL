#!/usr/bin/env python3
"""
Logger stress test script - calls various logging methods extensively
"""

import time
import json
import random
from WrenchCL import logger

def main():
    print("=" * 80)
    print("LOGGER STRESS TEST - 100+ CALLS")
    print("=" * 80)

    # Setup
    logger.enable_color()
    logger.start_time()

    # Test 1: Basic logging methods (50 calls)
    logger.header("Basic Logging Test")
    for i in range(15):
        logger.info(f"Info message #{i+1} - Everything is working fine")
        logger.debug(f"Debug message #{i+1} - Detailed debugging information")
        logger.warning(f"Warning message #{i+1} - Something might be wrong")
        if i % 5 == 0:
            logger.error(f"Error message #{i+1} - Something definitely went wrong!")
        if i % 10 == 0:
            logger.critical(f"Critical message #{i+1} - System is in danger!")

    # Test 2: Headers and formatting (20 calls)
    logger.header("Headers and Formatting Test")
    for i in range(10):
        logger.info(f"Message with header #{i+1}", header=f"Header {i+1}")
        logger.warning(f"Warning with header #{i+1}", header=f"Warning Header {i+1}")

    # Test 3: Data logging (15 calls)
    logger.header("Data Logging Test")
    sample_data = [
        {"name": "John", "age": 30, "city": "New York"},
        {"users": [1, 2, 3, 4, 5], "active": True, "config": {"debug": False}},
        [1, 2, 3, {"nested": "data"}, [4, 5, 6]],
        "Simple string data",
        {"large_object": {"a": 1, "b": 2, "c": {"d": 4, "e": [1, 2, 3, 4, 5]}}},
    ]

    for i, data in enumerate(sample_data):
        logger.data(data)
        logger.cdata(data)  # Compact version
        logger.info(f"Logged data item #{i+1}")

    # Test 4: Exception handling (10 calls)
    logger.header("Exception Handling Test")
    for i in range(5):
        try:
            # Simulate different types of errors
            if i == 0:
                raise ValueError(f"Sample ValueError #{i+1}")
            elif i == 1:
                raise KeyError(f"Sample KeyError #{i+1}")
            elif i == 2:
                raise FileNotFoundError(f"Sample FileNotFoundError #{i+1}")
            elif i == 3:
                raise AttributeError(f"Sample AttributeError #{i+1}")
            else:
                raise RuntimeError(f"Sample RuntimeError #{i+1}")
        except Exception as e:
            logger.error(f"Caught exception #{i+1}", exc_info=e)
            logger.exception(f"Exception handler #{i+1}")

    # Test 5: Mixed scenarios (20 calls)
    logger.header("Mixed Scenarios Test")
    log_methods = [logger.info, logger.warning, logger.error]

    for i in range(20):
        method = random.choice(log_methods)
        messages = [
            f"Random message #{i+1}",
            f"Processing item {i+1} of 20",
            f"Status update: {random.choice(['processing', 'completed', 'pending', 'failed'])}",
            f"Counter value: {i+1}, Random: {random.randint(1, 100)}"
        ]

        if i % 5 == 0:
            method(random.choice(messages), header=f"Batch {i//5 + 1}")
        else:
            method(random.choice(messages))

    # Test 6: Performance logging (10 calls)
    logger.header("Performance Logging Test")
    for i in range(10):
        start = time.time()
        # Simulate some work
        time.sleep(0.01)  # 10ms delay
        elapsed = time.time() - start
        logger.info(f"Operation #{i+1} completed in {elapsed:.3f}s")

    # Test 7: JSON-like data structures (10 calls)
    logger.header("JSON Data Structures Test")
    json_data = [
        {"api_response": {"status": 200, "data": {"users": [{"id": 1, "name": "Alice"}]}}},
        {"config": {"database": {"host": "localhost", "port": 5432, "ssl": True}}},
        {"metrics": {"cpu": 45.2, "memory": 78.5, "disk": 34.1, "network": {"in": 1024, "out": 2048}}},
        {"error_log": {"timestamp": "2024-01-01T12:00:00Z", "level": "ERROR", "message": "Database connection failed"}},
        {"batch_result": {"processed": 150, "failed": 3, "skipped": 2, "errors": ["timeout", "invalid_data", "network_error"]}}
    ]

    for i, data in enumerate(json_data):
        logger.data(data)
        logger.info(f"JSON structure #{i+1} logged")

    # Test 8: Rapid fire logging (30 calls)
    logger.header("Rapid Fire Test")
    for i in range(30):
        level = i % 4
        if level == 0:
            logger.debug(f"Rapid debug #{i+1}")
        elif level == 1:
            logger.info(f"Rapid info #{i+1}")
        elif level == 2:
            logger.warning(f"Rapid warning #{i+1}")
        else:
            logger.error(f"Rapid error #{i+1}")

    # Test 9: Large message test (5 calls)
    logger.header("Large Message Test")
    large_messages = [
        "This is a very long message " * 20,
        "Multi-line message\nLine 2\nLine 3\nLine 4\nLine 5",
        json.dumps({"large_array": list(range(100)), "description": "Large data structure"}),
        "Unicode test: 🚀 🌟 ✨ 🎉 🔥 💯 🎯 ⚡ 🌈 🎊",
        "Error details: " + "x" * 200  # Very long error message
    ]

    for i, msg in enumerate(large_messages):
        logger.info(f"Large message #{i+1}: {msg}")

    # Final summary
    logger.log_time("Total test duration")
    logger.header("Test Complete")
    logger.success("✅ All logging tests completed successfully!")

    # Display final stats
    total_calls = 15*5 + 10*2 + 5*3 + 5*2 + 20 + 10 + 5*2 + 30 + 5 + 3  # Approximate count
    logger.info(f"📊 Approximate total logging calls made: {total_calls}")
    logger.info(f"🎯 Logger performance test completed")

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()