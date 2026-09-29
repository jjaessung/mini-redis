"""Interactive command-line entry point for Mini Redis."""

from mini_redis import MiniRedis


def run_cli():
    """Run the Mini Redis read-eval-print loop."""
    redis = MiniRedis()

    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.strip().lower() in ("exit", "quit"):
            break

        result = redis.execute(line)
        if result is not None:
            print(result)


if __name__ == "__main__":
    run_cli()

