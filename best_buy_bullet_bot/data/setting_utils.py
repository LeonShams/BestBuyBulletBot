import json
import logging
import os.path
import shutil
import sys
from time import sleep

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from best_buy_bullet_bot.audio import sound_effects
from best_buy_bullet_bot.data import HEADLESS_WARNED, SHARED_DIR
from best_buy_bullet_bot.utils import (
    Colors,
    loading,
    print_table,
    validate_num,
    warnings_suppressed,
    yes_or_no,
)

SETTINGS_DIR = os.path.join(SHARED_DIR, "settings.json")
SOUND_MODES = ["disabled", "single", "repeat"]
DEFAULT_SETTINGS = {
    "funds": 1000,
    "tax": 0.095,
    "auto checkout": True,
    "account verification": True,
    "browser": "firefox",
    "sound mode": SOUND_MODES[2],
    "threads": 1,
}


def _save(data):
    with open(SETTINGS_DIR, "w+") as f:
        json.dump(data, f)


# Get the current settings
CURRENT_SETTINGS = DEFAULT_SETTINGS.copy()
if os.path.isfile(SETTINGS_DIR):
    save = False

    with open(SETTINGS_DIR) as f:
        for key, value in json.load(f).items():
            if key in CURRENT_SETTINGS:
                CURRENT_SETTINGS[key] = value
            elif not HEADLESS_WARNED():
                Colors.warn(
                    f"{key} is no longer supported and will be removed from your settings."
                )
                save = True

    if save and not HEADLESS_WARNED():
        if not warnings_suppressed() and yes_or_no(
            "Delete unsupported settings from your settings file (y/n): "
        ):
            _save(CURRENT_SETTINGS)
        HEADLESS_WARNED.update(True)
else:
    _save(DEFAULT_SETTINGS)


def get_settings():
    # A copy is returned so the settings can be safely manipulated
    return CURRENT_SETTINGS.copy()


def update_setting(setting, new_val):
    CURRENT_SETTINGS[setting] = new_val
    _save(CURRENT_SETTINGS)


def view_settings(show_default=False):
    settings = (DEFAULT_SETTINGS if show_default else CURRENT_SETTINGS).copy()

    settings["funds"] = f"${settings['funds']:,.2f}"
    settings["tax"] = f"{settings['tax'] * 100:.2f}%"
    settings["browser"] = settings["browser"].title()

    # Hidden property
    del settings["account verification"]

    rows = [[k.title(), v] for k, v in settings.items()]
    print_table(["Property", "Value"], rows)


def set_funds():
    while True:
        funds = input("Allotted money: $")
        funds = validate_num(funds.replace("$", ""), float)
        if funds is None or funds < 0:
            Colors.print(
                "Invalid input for funds. Please enter a positive number.",
                properties=["fail"],
            )
        else:
            break

    update_setting("funds", funds)
    Colors.print(f"Successfully set funds to ${funds:,.2f}!", properties=["success"])


def set_tax():
    while True:
        tax = input("Sales tax rate (%): ")
        tax = validate_num(tax.replace("%", ""), float)
        if tax is None or tax < 0:
            Colors.print(
                "Invalid input. Please enter a positive percentage for tax.",
                properties=["fail"],
            )
        else:
            break

    update_setting("tax", tax / 100)
    Colors.print(
        f"Successfully set the state sales tax rate to {tax:,.2f}%",
        properties=["success"],
    )


class MoneyManager:
    def get_funds(self):
        return CURRENT_SETTINGS["funds"]

    def check_funds(self, cost):
        return CURRENT_SETTINGS["funds"] - cost >= 0

    def make_purchase(self, cost):
        update_setting("funds", CURRENT_SETTINGS["funds"] - cost)


def _toggle_setting(setting_name):
    update_setting(setting_name, not CURRENT_SETTINGS[setting_name])
    Colors.print(
        f"Successfully {'enabled' if CURRENT_SETTINGS[setting_name] else 'disabled'} {setting_name}!",
        properties=["success"],
    )


def toggle_auto_checkout():
    _toggle_setting("auto checkout")


class DriverClassWrapper:
    def __init__(self, driver, manager, options):
        self.driver = driver
        self.manager = manager
        self.options = options


logging.disable(logging.WARNING)
DRIVER_NAMES = {
    "chrome": DriverClassWrapper(Chrome, ChromeDriverManager, ChromeOptions),
    "firefox": DriverClassWrapper(Firefox, GeckoDriverManager, FirefoxOptions),
}


def is_installed(browser_name):
    """Check if browser is installed

    Done by installing the drivers and trying to open the browser with selenium.
    If we can successfully open the browser then it is installed.
    """
    browser_name = browser_name.lower()

    if browser_name in DRIVER_NAMES:
        wrap = DRIVER_NAMES[browser_name]
    else:
        raise ValueError(
            f"3B Bot does not support {browser_name.title()}. Please pick either Chrome or Firefox."
        )

    # Install the drivers
    try:
        manager = wrap.manager()
        path = manager.install()
    except ValueError:
        return False

    options = wrap.options()
    options.add_argument("--headless")

    if CURRENT_SETTINGS["browser"] == "chrome":
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        # Try to open a browser window
        driver = wrap.driver(executable_path=path, options=options)
        driver.quit()
        return True

    except (WebDriverException, ValueError):
        # Delete the drivers we just installed
        name = manager.driver.get_name()
        driver_dir = path.split(name)[0] + name
        if os.path.isdir(driver_dir):
            shutil.rmtree(driver_dir)

        return False


def change_browser():
    with loading("Detecting browsers"):
        available_browsers = [
            browser.title() for browser in DRIVER_NAMES.keys() if is_installed(browser)
        ]

    if not len(available_browsers):
        Colors.print(
            "No available browsers. Please install either Chrome or Firefox and try again.",
            "Chrome can be installed from https://www.google.com/chrome/.",
            "Firefox can ben installed from https://www.mozilla.org/en-US/firefox/new/.",
            sep="\n",
            properties=["fail", "bold"],
        )
        sys.exit()

    # Print available browsers
    print("\n • ".join(["Available Browsers:"] + available_browsers), "\n")

    while True:
        new_browser = input("Select a browser from the list above: ").strip().title()

        if new_browser == "":
            continue

        if new_browser not in available_browsers:
            Colors.print("Invalid selection. Try again.", properties=["fail"])
        else:
            break

    update_setting("browser", new_browser.lower())
    Colors.print(
        f"Successfully changed browser to {new_browser}!", properties=["success"]
    )


def test_sound(repetitions=3, print_info=True):
    if print_info:
        print("Playing sound...")
        sleep(0.15)

    for i in range(repetitions):
        sound_effects.play(block=True)


def set_sound_mode():
    while True:
        sound_mode = input(
            f"Select a sound mode ({SOUND_MODES[0]}/{SOUND_MODES[1]}/{SOUND_MODES[2]}): "
        )
        if sound_mode not in SOUND_MODES:
            Colors.print(
                f'Invalid input for sound mode. Please enter either "{SOUND_MODES[0]}" (no sound),'
                f' "{SOUND_MODES[1]}" (plays sound once after coming back in stock), or "{SOUND_MODES[2]}"'
                " (plays sound repeatedly until item is no longer in stock).",
                properties=["fail"],
            )
        else:
            break

    update_setting("sound mode", sound_mode)
    Colors.print(
        f"Successfully set sound mode to {sound_mode}!", properties=["success"]
    )

    sleep(1)
    print("\nThat sounds like...")
    sleep(0.75)

    # No sound
    if sound_mode == SOUND_MODES[0]:
        sleep(0.5)
        print("Nothing. Crazy, right?")

    # Play sound once
    elif sound_mode == SOUND_MODES[1]:
        test_sound(repetitions=1, print_info=False)

    # Play sound on repeat
    elif sound_mode == SOUND_MODES[2]:
        test_sound(print_info=False)


def set_threads():
    while True:
        threads = input("Threads (per URL): ")
        threads = validate_num(threads, int)
        if threads is None or threads < 1:
            Colors.print(
                "Invalid number of threads. Please enter an integer greater than or equal to 1.",
                properties=["fail"],
            )
        else:
            break

    update_setting("threads", threads)
    Colors.print(
        f"Now using {threads} threads to track each URL!", properties=["success"]
    )


def reset_settings():
    print("Default settings:")
    view_settings(show_default=True)
    print()

    if yes_or_no("Reset (y/n): "):
        _save(DEFAULT_SETTINGS)
        Colors.print("Successfully reset settings!", properties=["success"])
    else:
        print("Settings reset aborted.")
