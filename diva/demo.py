#!/usr/bin/env python3
"""
Demo script for diva folder.
Usage: python3 demo.py [--name NAME]
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Demo script")
    parser.add_argument("--name", "-n", default="World", help="Name to greet")
    args = parser.parse_args()
    print(f"Hello, {args.name}! This is demo.py in the diva folder.")


if __name__ == "__main__":
    main()
