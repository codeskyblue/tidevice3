import threading

import pytest

from tidevice3.utils.common import print_dict_as_table, threadsafe_function


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
    # expect output:
    # a   bb
    # 123 2
    print_dict_as_table([{"a": 123, "bb": "2"}, {"a": 1}], headers=["a", "bb"], sep="-")
    captured = capsys.readouterr()
    expected_output = "".join([
        "a  -bb\n",
        "123-2\n",
        "1  -\n"
    ])
    assert captured.out == expected_output
    
    # expect output:
    # a bb
    print_dict_as_table([], headers=["a", "bb"], sep="-")
    captured = capsys.readouterr()
    assert captured.out == "a-bb\n"

