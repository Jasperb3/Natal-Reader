import os
import time
from functools import wraps
from datetime import datetime
from natal_reader.utils.constants import TIMESTAMP
from pathlib import Path

# Create relative path to timings directory
timings_dir = Path(__file__).parent.parent.parent.parent / "timings"
os.makedirs(timings_dir, exist_ok=True)

# Create file path with timestamp
timings_file_path = timings_dir / f"timeit_{TIMESTAMP}.txt"

# Initialize file only if it doesn't exist
if not os.path.exists(timings_file_path):
    with open(timings_file_path, "w") as f:
        f.write(f"Timing Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'⏱️ Function {func.__name__} took {total_time:.4f} seconds to complete\n')
        with open(timings_file_path, "a") as f:
            f.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - Function {func.__name__} took {total_time:.4f} seconds\n')
        return result
    return timeit_wrapper


def track_token_usage(func):
    @wraps(func)
    def track_token_usage_wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        token_usage = getattr(result, "token_usage", None)
        if token_usage is None:
            print(f"No token usage metrics available for {func.__name__}")
            return result

        token_count = token_usage.total_tokens
        print(f"🪙 Number of tokens used: {token_count:,}")
        with open(timings_file_path, "a") as f:
            f.write(f"{func.__name__} used {token_count:,} tokens\n")
        self.state.total_token_usage += token_count
        return result
    return track_token_usage_wrapper