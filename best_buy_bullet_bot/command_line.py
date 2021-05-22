import argparse

from best_buy_bullet_bot.data import setting_utils, url_utils, user_data
from best_buy_bullet_bot.tracker import start
from best_buy_bullet_bot.version import __version__


class NoAction(argparse.Action):
    def __init__(self, **kwargs):
        kwargs.setdefault("default", argparse.SUPPRESS)
        kwargs.setdefault("nargs", 0)
        super(NoAction, self).__init__(**kwargs)

    def __call__(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="3b-bot",
        description="Setup and control your best buy bot.",
        epilog="Good luck botting :)",
    )

    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )

    ops = {
        "start": [start, "Start tracking the currently set URLS."],
        "view-urls": [url_utils.view_urls, "View list of tracked URLS."],
        "add-url": [url_utils.add_url, "Add URL to tracking list."],
        "remove-url": [url_utils.remove_url, "Remove URL from list of tracked URLS."],
        "clear-urls": [url_utils.clear_urls, "Remove all tracked URLS."],
        "view-settings": [setting_utils.view_settings, "View current settings."],
        "set-funds": [
            setting_utils.set_funds,
            "Set how much money the bot is allowed to spend.",
        ],
        "set-tax": [setting_utils.set_tax, "Set the tax for your state."],
        "set-auto-checkout": [
            setting_utils.set_auto_checkout,
            "Enable/disable auto checkout.",
        ],
        "set-headless": [
            setting_utils.set_headless,
            "Enable/disable headless (browser visibility) checkout.",
        ],
        "set-sound": [
            setting_utils.set_sound,
            "Set sound to be completely disabled, to play once on item restock, or play repeatedly on item restock.",
        ],
        "set-speed": [
            setting_utils.set_speed,
            "Set how many threads to allocate to tracking each URL (will not affect auto checkout).",
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

    parser.add_argument(
        "COMMAND",
        default="start",
        const="start",
        nargs="?",
        choices=ops.keys(),
        help="Performs a specified operation.",
        metavar="command",
    )
    group = parser.add_argument_group(title="Available commands")

    for name, [func, help_msg] in ops.items():
        group.add_argument(name, help=help_msg, action=NoAction)

    args = parser.parse_args()
    ops[args.COMMAND][0]()
