from typing import List

def moving_average(nums: List[float], window: int) -> List[float]:
    """
    Compute the moving average over a sliding window.

    Args:
        nums: a list of numbers (ints or floats)
        window: size of the sliding window; must be a positive integer

    Returns:
        A list of averages, one for each window position.

    Raises:
        TypeError: if nums is not a list or window is not an int
        ValueError: if window is not positive
    """
    if not isinstance(nums, list):
        raise TypeError("nums must be a list of numbers")
    if not isinstance(window, int):
        raise TypeError("window must be an integer")
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(nums):
        raise ValueError("window must not be larger than the list size")

    averages: List[float] = []
    for i in range(len(nums) - window + 1):
        window_sum = sum(nums[i : i + window])
        averages.append(window_sum / window)

    return averages