import json
import os
import sys
import tempfile
from glob import glob

from best_buy_bullet_bot.utils import Colors


def _read_file():
    FP.seek(0)
    return json.load(FP)


def _write_file(content):
    FP.seek(0)
    FP.write(json.dumps(content))
    FP.truncate()


# This function is called before killing all processes to
# make sure the temp file is deleted
def close_data():
    FP.close()
    if num_temp_files == 1 and os.path.isfile(FP.name):
        os.remove(FP.name)


# Windows doesn't allow for temporary files to be opened by a subprocess
# by default so we have to pass a flag to do so
def temp_opener(name, flag, mode=0o777):
    return os.open(name, flag | os.O_TEMPORARY, mode)


# TODO: Prevent directory from changing based on whether or not we are in root
temp_dir = os.path.dirname(tempfile.mkdtemp())

prefix = "best_buy_bullet_bot_global_vars"
suffix = ".json"
available_temp_files = glob(os.path.join(temp_dir, f"{prefix}*{suffix}"))
num_temp_files = len(available_temp_files)


if num_temp_files == 1:
    # Open the existing temp file
    FP = open(
        os.path.join(temp_dir, available_temp_files[0]),
        "r+",
        opener=temp_opener if sys.platform == "win32" else None,
    )
else:
    if num_temp_files > 1:
        # Too many temp files
        Colors.warn(
            f"Too many temporary files detected: {available_temp_files}. Deleting all temporary files."
        )
        for filename in available_temp_files:
            os.remove(os.path.join(temp_dir, filename))

    # Create a new temp file since we don't have any
    FP = tempfile.NamedTemporaryFile("r+", prefix=prefix, suffix=suffix, dir=temp_dir)
    _write_file({})


class ReferenceVar:
    """Points to a specific variable in the temp file.

    If a variale in changed by one process all other processes
    with that variable will receive that change when trying to
    access the variable.
    """

    def __init__(self, var_name):
        self.var_name = var_name

    def __new__(cls, var_name):
        # Return the value of the variable if it is a constant
        # else return this object
        self = super().__new__(cls)
        self.__init__(var_name)
        return self() if var_name.endswith("constant") else self

    def __call__(self):
        return _read_file()[self.var_name]

    def update(self, new_value, constant=False):
        # Update the value of the variable in the temp file
        updated_dict = _read_file()

        new_name = self.var_name
        new_name += "_constant" if constant else ""
        updated_dict.update({new_name: new_value})
        _write_file(updated_dict)

        return new_value if constant else self


if num_temp_files != 1:
    # We are in the main process. This is where variables are created.

    from keyring.util import platform_

    # We store data here so it doesn't get overwritten during an update
    shared_dir = os.path.join(
        os.path.dirname(platform_.data_root()), "best_buy_bullet_bot"
    )
    if not os.path.isdir(shared_dir):
        os.makedirs(shared_dir)

    # Save to temporary file
    HEADLESS_WARNED = ReferenceVar("HEADLESS_WARNED").update(False)
    SHARED_DIR = ReferenceVar("SHARED_DIR").update(shared_dir, constant=True)
else:
    # We are in a separate process. This is where variables are copied over from the main process.

    # Copy over all variables in the temp file to the locals dict so they can be imported
    for var_name in _read_file():
        locals()[var_name.replace("_constant", "")] = ReferenceVar(var_name)
