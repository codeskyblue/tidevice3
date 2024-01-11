import threading

import pytest
from tidevice3.utils.common import threadsafe_function, print_dict_as_table

def test_threadsafe_function():
    # Define a shared variable
    shared_variable = 0

    # Define a threadsafe function
    @threadsafe_function
    def increment_shared_variable():
        nonlocal shared_variable
        shared_variable += 1

    # Define a helper function to run the threads
    def run_threads():
        for _ in range(1000):
            increment_shared_variable()

    # Create multiple threads to increment the shared variable
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=run_threads)
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Check if the shared variable has been incremented correctly
    assert shared_variable == 10000


def test_print_dict_as_table(capsys: pytest.CaptureFixture[str]):
    print_dict_as_table([{"a": 123, "bb": "2"}], headers=["a", "bb"], sep="-")
    # expect output:
    # a   bb
    # 123 2
    # Use capsys to capture stdout
    captured = capsys.readouterr()

    # Define the expected output
    expected_output = "".join([
        "a  -bb\n",
        "123-2\n",
    ])

    # Assert that the actual output matches the expected output
    assert captured.out == expected_output
