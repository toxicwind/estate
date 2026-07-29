def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer n.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# Example usage:
if __name__ == "__main__":
    # Test cases
    for i in range(6):
        print(f"{i}! = {factorial(i)}")