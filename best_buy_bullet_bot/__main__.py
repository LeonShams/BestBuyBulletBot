import sys

from rich.traceback import install

from best_buy_bullet_bot.command_line import run_command


def main():
    # Stylizes errors and shows more info
    install()

    try:
        run_command()
    except KeyboardInterrupt:
        # This way we don't get the keyboardinterrupt traceback error
        sys.exit(0)


# Running things directly can be useful in development
if __name__ == "__main__":
    main()
