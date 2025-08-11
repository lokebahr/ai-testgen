# calculator.py
def divide(a, b):
    """Return the result of a / b."""
    return a / b  # Potential ZeroDivisionError

def factorial(n):
    """Return n! for n >= 0."""
    if n < 0:
        raise ValueError("Negative values not allowed")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def average(numbers):
    """Return the average of a list of numbers."""
    return sum(numbers) / len(numbers)  # Edge case: empty list
