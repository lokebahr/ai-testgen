import os

def read_file(filename):
    """Read and return the contents of the file with appropriate error handling."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("Filename must be a non-empty string.")
    if os.path.isdir(filename):
        raise IsADirectoryError("The provided path is a directory, expected a file.")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except PermissionError as e:
        raise PermissionError(f"Cannot read file due to permission error: {e}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e}")

if __name__ == "__main__":
    # Edge case: tries to read a file outside intended directory
    print(read_file("../../etc/passwd")) #test