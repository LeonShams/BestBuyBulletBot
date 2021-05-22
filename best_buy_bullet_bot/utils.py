from threading import Event

from tqdm import tqdm


class bcolors:
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    _ENDC = "\033[0m"

    @staticmethod
    def _props2str(props):
        return "".join([getattr(bcolors, prop.upper()) for prop in props])

    @staticmethod
    def str(string, properties=[]):
        return bcolors._props2str(properties) + string + bcolors._ENDC

    @staticmethod
    def print(*args, properties=[], **kwargs):
        print(bcolors._props2str(properties), end="")
        print_end = kwargs.pop("end", "\n")
        print(*args, **kwargs, end=bcolors._ENDC + print_end)


class IndefeniteProgressBar:
    def __init__(self):
        def generator():
            while True:
                yield

        self.pbar = tqdm(generator())

    def update(self):
        self.pbar.update(1)

    def close(self):
        self.pbar.close()


class TwoWayPause:
    def __init__(self):
        self._terminated = False
        self.play = Event()
        self.play.set()
        self.pause = Event()

    def is_set(self):
        return self.pause.is_set()

    def is_terminated(self):
        return self._terminated

    def set(self, terminate=False):
        self._terminated = terminate
        self.play.clear()
        self.pause.set()

    def clear(self):
        self.pause.clear()
        self.play.set()

    def wait(self):
        self.pause.wait()

    def wait_inverse(self):
        self.play.wait()


def validate_num(val, dtype):
    try:
        cast_val = dtype(val)
    except ValueError:
        return

    if dtype is int and cast_val != float(val):
        return
    return cast_val


def yes_or_no(prompt):
    while True:
        response = input(prompt).lower()
        if response not in ["y", "n"]:
            bcolors.print(
                'Invalid response. Please enter either "y" or "n"', properties=["fail"]
            )
        else:
            return response == "y"
