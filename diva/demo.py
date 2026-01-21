"""Simple demo script in the diva package.

This module provides a tiny command-line program that greets the provided
name. It is intended as a minimal example demonstrating how to structure a
script with a main() entry point.
"""

import argparse


def main():
    """Parse command-line arguments and print a greeting.

    The function uses argparse to accept an optional --name / -n argument.
    If not provided it defaults to "World".

    This function is written so it can be imported and called from tests or
    used directly when the module is executed as a script.
    """
    parser = argparse.ArgumentParser(description="Demo script")
    parser.add_argument("--name", "-n", default="World", help="Name to greet")
    args = parser.parse_args()
    print(f"Hello, {args.name}! This is demo.py in the diva folder.")


if __name__ == "__main__":
    main()
