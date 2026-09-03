"""
Main entry point for TestProject.
"""

def get_hello_message(name: str = "World") -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"

def main() -> None:
    """Main execution function."""
    message = get_hello_message()
    print(message)

if __name__ == "__main__":
    main()
