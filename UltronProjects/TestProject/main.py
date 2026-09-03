def get_greeting(name: str = "World") -> str:
    return f"Hello, {name}!"

def main():
    greeting = get_greeting()
    print(greeting)

if __name__ == "__main__":
    main()
