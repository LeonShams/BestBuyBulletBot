import sys
import time
from collections import deque
from datetime import timedelta

from rich import get_console
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TextColumn


class TimeRemainingColumn(ProgressColumn):
    """Renders estimated time remaining."""

    # Only refresh twice a second to prevent jitter
    max_refresh = 0.5

    def __init__(self, *args, **kwargs):
        self.start_time = time.time()
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        delta = timedelta(seconds=int(time.time() - self.start_time))
        return str(delta)


class IterationsPerSecond:
    def format(self, task):
        if "times" in dir(task) and len(task.times):
            speed = len(task.times) / task.times[-1]
            return f"{speed:.2f}it/s"
        return "0.00it/s"


class IndefeniteProgressBar:
    def __init__(self):
        with get_console() as console:
            self.pbar = Progress(
                SpinnerColumn(style=""),
                TextColumn("{task.completed}it"),
                BarColumn(console.width),
                TextColumn(IterationsPerSecond()),
                TimeRemainingColumn(),
                console=console,
                expand=True,
            )

        self.pbar.start()
        self.pbar.add_task(None, start=False)
        self.pbar.tasks[0].times = deque(maxlen=100)
        self.start_time = time.time()

    def print(self, *args, sep=" ", end="\n"):
        msg = sep.join(map(str, args))
        sys.stdout.writelines(msg + end)

    def update(self):
        task = self.pbar.tasks[0]
        task.completed += 1
        task.times.append(time.time() - self.start_time)

    def close(self):
        self.pbar.stop()
