"""
diva/diva.py
Utility module that provides simple numeric helpers.

Usage:
- As a module: from diva.diva import second_largest
- As a script: python3 diva/diva.py 3 5 2 8
  or run without args and it will prompt for a comma-separated list of numbers.

This file used to implement add_numbers; that function is retained for compatibility,
but the primary new functionality is `second_largest` which returns the second-
largest distinct numeric value from an input sequence.
"""

from typing import Iterable, Union, List

NumberLike = Union[int, float, str]


def add_numbers(a, b):
    """Return the sum of two numbers.

    Kept for backward compatibility. Accepts integers or floats (or strings
    that can be converted to float).
    """
    try:
        return float(a) + float(b)
    except (TypeError, ValueError):
        raise ValueError("Both inputs must be numbers or numeric strings")


def _to_number(x: NumberLike) -> float:
    """Convert a single value to float, raising ValueError for invalid input."""
    try:
        return float(x)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid numeric value: {x!r}")


def second_largest(values: Iterable[NumberLike]) -> float:
    """Return the second-largest distinct numeric value from values.

    - values: an iterable of numbers or numeric strings.
    - The function considers distinct values: if the input is [5, 5, 3]
      the second largest is 3, not 5.
    - Raises ValueError if there are fewer than two distinct numeric values.
    """
    nums: List[float] = [_to_number(v) for v in values]
    if len(nums) < 2:
        raise ValueError("Need at least two numeric values to determine second largest")

    # Use a set to find distinct values, then pick the second largest.
    distinct = set(nums)
    if len(distinct) < 2:
        raise ValueError("Need at least two distinct numeric values to determine second largest")

    # Remove the maximum then take the max of the remainder
    max_val = max(distinct)
    distinct.remove(max_val)
    second = max(distinct)
    return second


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Find the second-largest distinct number")
    parser.add_argument("numbers", nargs="*", help="Numbers (space separated). If omitted you will be prompted for a comma-separated list.")
    args = parser.parse_args()

    raw_nums = args.numbers
    if not raw_nums:
        try:
            s = input("Enter numbers (comma-separated): ")
        except EOFError:
            print("No input provided.")
            sys.exit(1)
        # allow comma or space separated input
        if "," in s:
            raw_nums = [p.strip() for p in s.split(",") if p.strip()]
        else:
            raw_nums = [p for p in s.split() if p]

    try:
        result = second_largest(raw_nums)
        # print as int if whole number
        if result.is_integer():
            print(int(result))
        else:
            print(result)
    except ValueError as e:
        print("Error:", e)
        sys.exit(1)