import threading
import time
from tidevice3.utils.common import threadsafe_function

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
