import os
from threading import Event, Thread

from playsound import playsound

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification.wav")
playing = Event()


def _repeat():
    while True:
        playing.wait()
        playsound(path)


repeat_loop = Thread(target=_repeat, daemon=True)
repeat_loop.start()


def play(block=False):
    playsound(path, block)


def start():
    playing.set()


def stop():
    playing.clear()
