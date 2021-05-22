import json
import os

import termtables as tt
from best_buy_bullet_bot.utils import bcolors, validate_num

URL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.json")


def _read():
    with open(URL_DIR, mode="r") as f:
        return json.load(f)


def _save(data):
    with open(URL_DIR, "w") as f:
        json.dump(data, f)


def get_url_data():
    return _read().items()


def view_urls(show_qty=True, max_url_chars=None):
    data = get_url_data()
    tt.print(
        [
            [url[:max_url_chars] + ("..." if len(url) > max_url_chars else "")]
            + ([qty] if show_qty else [])
            for url, qty in data
        ]
        if len(data)
        else [["", ""]],
        header=["URL", "Quantity"],
    )


def add_url():
    new_url = input("URL to add: ")
    if new_url.strip() == "":
        print("Aborted.")
        return

    while True:
        qty = input("Quantity (optional): ")

        if qty.strip() == "" or qty == "inf":
            qty = "inf"
            break

        qty = validate_num(qty, int)
        if qty == None or qty < 0:
            bcolors.print(
                "Invaild input for quantity. Please enter a positive integer.",
                properties=["fail"],
            )
        else:
            break

    urls = _read()
    urls[new_url] = qty
    _save(urls)
    bcolors.print(
        f"Successfully added {new_url}{'' if qty == 'inf' else f' with a quantity of {qty}'}!",
        properties=["success"],
    )


def remove_url():
    urls = _read()
    print("Active urls:\n" + "\n".join(urls.keys()) + "\n")

    url = input("URL to remove: ")
    if urls.pop(url, None) is None:
        bcolors.print(f"Unable to find the url {url}", properties=["fail"])
    else:
        _save(urls)
        bcolors.print(f"Successfully removed {url}", properties=["success"])


def clear_urls():
    _save({})
    bcolors.print(f"Successfully removed all urls!", properties=["success"])
