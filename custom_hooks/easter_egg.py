import glob
import os.path
from pathlib import Path


def calculate_indentation(string):
    return string[: string.index(string.strip())]


def starts_with(string, *substrings, begin=0, end=None):
    starts_with_substring = list(map(string[begin:end].startswith, substrings))
    if any(starts_with_substring):
        return substrings[starts_with_substring.index(True)]
    return False


MSG = '''"""
EASTER EGG: Thank you for reading the source code!
To run the bot with a higher priority level and achieve better performance complete the following.

If using Firefox, complete the following before moving on to the next step:
WINDOWS: Open a Command Prompt window with "Run as administrator" https://www.educative.io/edpresso/how-to-run-cmd-as-an-administrator
MAC: Enter the command `su` in your terminal to gain root privileges. Beware your settings may be different in the root session, but you can always return to a normal session with the `exit` command.

Then regardless of your browser:
Run `3b-bot --fast` in your shell.
"""'''

split_msg = MSG.split("\n")


def indent_msg(indent):
    return "\n".join(
        [indent + msg_line if msg_line.strip() else "" for msg_line in split_msg]
    )


if __name__ == "__main__":
    # Get path of best_buy_bullet_bot directory
    parent_dir = Path(__file__).parents[1]
    search_dir = os.path.join(parent_dir, "best_buy_bullet_bot")

    for filename in glob.iglob(os.path.join(search_dir, "**"), recursive=True):
        # Skip if not a python file
        if not filename.endswith(".py"):
            continue

        with open(filename, "r+") as f:
            code = f.read()
            lowercase_code = code.lower()

            # Skip file if no easter egg comments need to be added
            if "easter egg" not in lowercase_code:
                continue

            lines = code.split("\n")
            lower_lines = lowercase_code.split("\n")

            for idx, line in enumerate(lines):
                line = line.lower().strip()

                # Skip line if the text "easter egg" is not in it
                if "easter egg" not in line:
                    continue

                # This variable means we will delete the following lines until we find a line that ends in the variable
                clear_multiline_string = starts_with(line, "'''", '"""')

                # If the multiline comment starts on the previous line
                if not clear_multiline_string and not starts_with(line, "'", '"', "#"):
                    previous_line = lines[idx - 1]
                    indent = calculate_indentation(previous_line)

                    previous_line = previous_line.strip()
                    clear_multiline_string = starts_with(previous_line, "'''", '"""')

                    if clear_multiline_string:
                        # Delete the previous line
                        lines.pop(idx - 1)
                        idx -= 1
                    else:
                        # Its not a comment, just the text "easter egg" laying around somewhere
                        continue
                else:
                    indent = calculate_indentation(lines[idx])

                if clear_multiline_string:
                    # Delete all subsequent lines until the comment ends
                    while not lines[idx + 1].strip().endswith(clear_multiline_string):
                        lines.pop(idx + 1)
                    lines.pop(idx + 1)

                # Replace the current line with the correct message
                lines.pop(idx)
                lines.insert(idx, indent_msg(indent))

            easter_egg_code = "\n".join(lines)

            # Update the file with the new code
            if easter_egg_code != code:
                f.seek(0)
                f.write(easter_egg_code)
                f.truncate()
