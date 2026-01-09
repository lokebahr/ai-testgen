# user_login.py
USERS = {
    "Alice": "Password123",
    "Bob": "hunter2"
}

def login(username, password):
    """Return True if username/password match."""
    if username in USERS and USERS[username] == password:
        return True
    return False

if __name__ == "__main__":
    print(login("alice", "Password123"))  # Should fail, but edge case is casing
