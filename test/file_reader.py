# file_reader.py
import os

def read_file(filename):
    """Read and return the contents of the file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == "__main__":
    # Edge case: tries to read a file outside intended directory
    print(read_file("../../etc/passwd"))
