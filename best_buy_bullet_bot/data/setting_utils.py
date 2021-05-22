import json
import os

import termtables as tt
from best_buy_bullet_bot.utils import bcolors, validate_num

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
SOUND_MODES = ["disabled", "single", "repeat"]
DEFAULT_SETTINGS = {
    "Funds": 1000,
    "Tax": 0.095,
    "Auto Checkout": True,
    "Headless": False,
    "Sound Mode": SOUND_MODES[2],
    "Speed": 2,
}


def get_settings():
    with open(SETTINGS_DIR, mode="r") as f:
        current_settings = json.load(f)
    if len(current_settings) != len(DEFAULT_SETTINGS):
        _save(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    else:
        return current_settings


def _save(data):
    with open(SETTINGS_DIR, "w") as f:
        json.dump(data, f)


def view_settings(show_default=False):
    settings = DEFAULT_SETTINGS.copy() if show_default else get_settings()
    settings["Funds"] = f"${settings['Funds']:,.2f}"
    settings["Tax"] = f"{settings['Tax'] * 100:.2f}%"
    tt.print(list(map(list, settings.items())))


def set_funds():
    while True:
        funds = input("Allotted money: $")
        funds = validate_num(funds.replace("$", ""), float)
        if funds is None or funds < 0:
            bcolors.print(
                "Invaild input for funds. Please enter a positive number.",
                properties=["fail"],
            )
        else:
            break

    settings = get_settings()
    settings["Funds"] = funds
    _save(settings)
    bcolors.print(f"Successfully set funds to ${funds:,.2f}!", properties=["success"])


def set_tax():
    while True:
        tax = input("Tax (%): ")
        tax = validate_num(tax.replace("%", ""), float)
        if tax is None or tax < 0:
            bcolors.print(
                "Invaild input. Please enter a positive percentage for tax.",
                properties=["fail"],
            )
        else:
            break

    settings = get_settings()
    settings["Tax"] = tax / 100
    _save(settings)
    bcolors.print(f"Successfully set tax to {tax:,.2f}%", properties=["success"])


class MoneyManager:
    def __init__(self):
        self.settings = get_settings()

    def get_funds(self):
        return self.settings["Funds"]

    def check_funds(self, cost):
        return self.settings["Funds"] - cost >= 0

    def make_purchase(self, cost):
        self.settings["Funds"] -= cost
        _save(self.settings)


def set_auto_checkout():
    while True:
        auto_checkout = input("Would you like to enable autocheckout (y/n): ")
        if auto_checkout.lower() not in ["yes", "no", "y", "n"]:
            bcolors.print(
                'Invalid input for auto checkout. Please enter either "y" or "n".',
                properties=["fail"],
            )
        else:
            break

    auto_checkout = auto_checkout[0] == "y"
    settings = get_settings()
    settings["Auto Checkout"] = auto_checkout
    _save(settings)
    bcolors.print(
        f"Successfully {'enabled' if auto_checkout else 'disabled'} auto checkout!",
        properties=["success"],
    )


def set_headless():
    while True:
        headless = input("Would you like to enable headless checkout (y/n): ")
        if headless.lower() not in ["yes", "no", "y", "n"]:
            bcolors.print(
                'Invalid input for the headless setting. Please enter either "y" or "n".',
                properties=["fail"],
            )
        else:
            break

    headless = headless[0] == "y"
    settings = get_settings()
    settings["Headless"] = headless
    _save(settings)
    bcolors.print(
        f"Successfully {'enabled' if headless else 'disabled'} headless auto checkout!",
        properties=["success"],
    )


def set_sound():
    while True:
        sound_mode = input(
            f"Select a sound mode ({SOUND_MODES[0]}/{SOUND_MODES[1]}/{SOUND_MODES[2]}): "
        )
        if sound_mode not in SOUND_MODES:
            bcolors.print(
                f'Invalid input for sound mode. Please enter either "{SOUND_MODES[0]}" (no sound),'
                f' "{SOUND_MODES[1]}" (plays sound once after coming back in stock), or "{SOUND_MODES[2]}"'
                " (plays sound repeatedly until item is no longer in stock).",
                properties=["fail"],
            )
        else:
            break

    settings = get_settings()
    settings["Sound Mode"] = sound_mode
    _save(settings)
    bcolors.print(
        f"Successfully set sound mode to {sound_mode}!", properties=["success"]
    )


def set_speed():
    while True:
        speed = input("Speed (num of threads per URL): ")
        speed = validate_num(speed, int)
        if speed is None or speed < 1:
            bcolors.print(
                "Invaild input for speed. Please enter an integer greater than or equal to 1.",
                properties=["fail"],
            )
        else:
            break

    settings = get_settings()
    settings["Speed"] = speed
    _save(settings)
    bcolors.print(f"Successfully set speed to {speed}!", properties=["success"])


def reset_settings():
    print("Default settings:")
    view_settings(show_default=True)
    print()
    while True:
        reset = input("Reset (y/n): ")
        if reset.lower() not in ["yes", "no", "y", "n"]:
            bcolors.print(
                'Invalid input for the reset. Please enter either "y" or "n".',
                properties=["fail"],
            )
        else:
            break

    if reset[0] == "y":
        _save(DEFAULT_SETTINGS)
        bcolors.print(f"Successfully reset settings!", properties=["success"])
    else:
        print("Settings reset aborted.")
