def get_greeting(name: str = "World") -> str:
    """Generates a greeting message."""
    return f"Hello, {name}!"


def main() -> None:
    """Main entry point of the application."""
    message = get_greeting()
    print(message)


if __name__ == "__main__":
    main()
