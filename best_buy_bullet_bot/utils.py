import warnings

import psutil
from rich import get_console
from rich.columns import Columns
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table


def _pretty_warning(msg, *args, **kwargs):
    return Colors.str(f"WARNING: {msg}\n", properties=["warning"])


warnings.formatwarning = _pretty_warning


class Colors:
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    _ENDC = "\033[0m"

    @staticmethod
    def _props2str(props):
        return "".join([getattr(Colors, prop.upper()) for prop in props])

    @staticmethod
    def str(string, properties=[]):
        return Colors._props2str(properties) + string + Colors._ENDC

    @staticmethod
    def print(*args, properties=[], **kwargs):
        print(Colors._props2str(properties), end="")
        print_end = kwargs.pop("end", "\n")
        print(*args, **kwargs, end=Colors._ENDC + print_end)

    @staticmethod
    def warn(*args, **kwargs):
        warnings.warn(*args, **kwargs)


def print_table(columns, rows, justifications=["left", "center"]):
    table = Table(show_lines=True)
    for i, column in enumerate(columns):
        table.add_column(column, justify=justifications[i])

    for row in rows:
        row = list(map(str, row))
        max_lines = max(string.count("\n") for string in row)
        vert_align_row = [
            "\n" * int((max_lines - string.count("\n")) / 2) + string for string in row
        ]
        table.add_row(*vert_align_row)

    with get_console() as console:
        console.print(table)


def count_cores():
    cores = psutil.cpu_count(logical=False)
    print("Cores:", cores)
    threads = psutil.cpu_count(logical=True) / cores
    int_threads = int(threads)
    if int_threads == threads:
        print("Threads per core:", int_threads)


def warnings_suppressed():
    return any(
        [filter[0] == "ignore" and filter[2] is Warning for filter in warnings.filters]
    )


def loading(msg):
    loading_text = Columns([msg, Spinner("simpleDotsScrolling")])
    return Live(loading_text, refresh_per_second=5, transient=True)


def yes_or_no(prompt):
    while True:
        response = input(prompt).lower().strip()

        if response == "":
            continue

        if response in "yes" or response in "no":
            return response in "yes"
        else:
            Colors.print(
                'Invalid response. Please enter either "y" or "n"', properties=["fail"]
            )


def validate_num(val, dtype):
    try:
        cast_val = dtype(val)
    except ValueError:
        return

    if dtype is int and cast_val != float(val):
        return
    return cast_val
