import argparse
import warnings

from best_buy_bullet_bot.utils import count_cores
from best_buy_bullet_bot.version import __version__


class NoAction(argparse.Action):
    """Makes argument do nothing.

    This is useful if we want an argument to show up in the
    help menu, but remain uncallable.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("default", argparse.SUPPRESS)
        kwargs.setdefault("nargs", 0)
        super().__init__(**kwargs)

    def __call__(self, *args):
        pass


class FuncKwargs(dict):
    """Only passes flags to a specified function."""

    def __init__(self, args):
        self.args = args
        super().__init__()

    def add_flag(self, flag_name, cmd_name):
        flag = getattr(self.args, flag_name)
        flag and self.args.cmd == cmd_name and self.update({flag_name: flag})


class ImportWrapper:
    """Only imports the function that the user selects."""

    def __init__(self, file):
        self.file = file

    def __getattribute__(self, name):
        if name == "file":
            return super().__getattribute__("file")

        def call_func(*args, **kwargs):
            imported_file = __import__(self.file, fromlist=[""])
            return getattr(imported_file, name)(*args, **kwargs)

        return call_func


# This is done to prevent unnecessary imports and more importantly
# prevent a bunch of warnings from setting_utils when imported
tracker = ImportWrapper("best_buy_bullet_bot.tracker")
setting_utils = ImportWrapper("best_buy_bullet_bot.data.setting_utils")
url_utils = ImportWrapper("best_buy_bullet_bot.data.url_utils")
user_data = ImportWrapper("best_buy_bullet_bot.data.user_data")
browser_login = ImportWrapper("best_buy_bullet_bot.data.browser_login")

OPS = {
    "start": [tracker.start, "Start tracking the currently set URLs."],
    "view-urls": [url_utils.view_urls, "View list of tracked URLs."],
    "add-url": [url_utils.add_url, "Add URL to tracking list."],
    "add-url-group": [
        url_utils.add_url_group,
        "Add multiple URLs and set a quantity for all of them as a whole instead of individually.",
    ],
    "remove-url": [
        url_utils.remove_url,
        "Remove a URL from the list of tracked URLs.",
    ],
    "test-urls": [
        url_utils.test_urls,
        "Tests to make sure all URLs can be tracked. This is also run on startup.",
    ],
    "clear-urls": [url_utils.clear_urls, "Remove all tracked URLs."],
    "view-settings": [setting_utils.view_settings, "View current settings."],
    "set-funds": [
        setting_utils.set_funds,
        "Set how much money the bot is allowed to spend.",
    ],
    "set-tax": [setting_utils.set_tax, "Set the sales tax rate for your state."],
    "toggle-auto-checkout": [
        setting_utils.toggle_auto_checkout,
        "Enable/disable auto checkout.",
    ],
    "change-browser": [
        setting_utils.change_browser,
        "Pick the browser to be used during tracking and auto-checkout (only applies if auto-checkout is enabled). \
            Firefox is the default and recommended browser.",
    ],
    "test-sound": [setting_utils.test_sound, "Play sound sample."],
    "set-sound-mode": [
        setting_utils.set_sound_mode,
        "Choose whether you want sound to be completely disabled, play once on item restock, or play repeatedly on item restock.",
    ],
    "set-threads": [
        setting_utils.set_threads,
        "Select the number of threads to allocate to tracking each URL.",
    ],
    "count-cores": [
        count_cores,
        "Print how many CPU cores you have and how many threads each core has.",
    ],
    "reset-settings": [
        setting_utils.reset_settings,
        "Reset setting to the defaults.",
    ],
    "view-creds": [
        user_data.print_creds,
        "View your Best Buy login credentials (email, password, cvv).",
    ],
    "set-creds": [
        user_data.set_creds,
        "Set your Best Buy login credentials (email, password, cvv).",
    ],
    "clear-creds": [
        user_data.clear_creds,
        "Reset your Best Buy login credentials (email, password, cvv). Also offers the option to reset your access password.",
    ],
}


def run_command():
    parser = argparse.ArgumentParser(
        prog="3b-bot",
        description="Setup and control your Best Buy bot.",
        epilog="Good luck :)",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + __version__,
        help="show 3B Bot version number",
    )

    parser.add_argument(
        "cmd",
        default="start",
        const="start",
        nargs="?",
        choices=OPS.keys(),
        help="Performs a specified operation.",
        metavar="command",
        type=str.lower,
    )
    group = parser.add_argument_group(title="Available commands")

    for name, [func, help_msg] in OPS.items():
        group.add_argument(name, help=help_msg, action=NoAction)

    parser.add_argument(
        "-w", "--suppress-warnings", action="store_true", help="suppress warnings"
    )

    """
    EASTER EGG: Thank you for reading the source code!
    To run the bot with a higher priority level and achieve better performance complete the following.

    If using Firefox, complete the following before moving on to the next step:
    WINDOWS: Open a Command Prompt window with "Run as administrator" https://www.educative.io/edpresso/how-to-run-cmd-as-an-administrator
    MAC: Enter the command `su` in your terminal to gain root privileges. Beware your settings may be different in the root session, but you can always return to a normal session with the `exit` command.

    Then regardless of your browser:
    Run `3b-bot --fast` in your shell.
    """
    parser.add_argument("--fast", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--headless", action="store_true", help="hide the browser during auto checkout"
    )
    parser.add_argument(
        "--verify-account",
        action="store_true",
        help="confirm that the account is setup properly (automatically performed on first run)",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="skip checks on first run that make sure account is setup properly.",
    )
    parser.add_argument(
        "--force-login",
        action="store_true",
        help="force browser to go through traditional login process as opposed to using cookies to skip steps",
    )

    args = parser.parse_args()
    func_kwargs = FuncKwargs(args)

    func_kwargs.add_flag("fast", "start")
    func_kwargs.add_flag("headless", "start")
    func_kwargs.add_flag("verify_account", "start")
    func_kwargs.add_flag("skip_verification", "start")

    if args.suppress_warnings:
        warnings.filterwarnings("ignore")
    else:
        # Just ignore the depreciation warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    if args.force_login:
        browser_login.delete_cookies()

    # Run command
    OPS[args.cmd][0](**func_kwargs)
