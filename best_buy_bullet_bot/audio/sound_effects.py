import os

import openal

# Loading the sound effect
source = openal.oalOpen(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "notification.wav")
)


def play_sound():
    if source._exitsts:
        source.set_looping(False)
        source.rewind()
        source.play()


def start_sound():
    if source._exitsts:
        source.set_looping(True)
        source.rewind()
        source.play()


def stop_sound():
    if source._exitsts:
        source.stop()


def destroy(windows):
    if windows:
        openal.oalQuit()
    else:
        if source._exitsts:
            if source.get_state() == 4114:
                stop_sound()
            source.destroy()
