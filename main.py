import uuid
from agent import run_agent


def main():
    session_id = str(uuid.uuid4())
    print("🎬 CineAgent (terminal mode) — type 'exit' or 'quit' to end\n")
    print("Agent: What kind of mood are you in? (or name a movie)\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not message:
            continue
        if message.lower() in ("exit", "quit"):
            print("Exiting.")
            break

        response = run_agent(session_id, message)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()
