import json
import os.path

from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util.retry import Retry

from best_buy_bullet_bot.browser import get_user_agent
from best_buy_bullet_bot.data import SHARED_DIR
from best_buy_bullet_bot.utils import (
    Colors,
    loading,
    print_table,
    validate_num,
    yes_or_no,
)

URL_DIR = os.path.join(SHARED_DIR, "urls.json")


def _read():
    with open(URL_DIR) as f:
        return json.load(f)


def _save(data):
    with open(URL_DIR, "w+") as f:
        json.dump(data, f)


if not os.path.isfile(URL_DIR):
    _save({})


def get_url_data():
    items = _read().items()
    return [[item.split("\n"), qty] for item, qty in items]


def view_urls(show_qty=True):
    data = _read().items()

    columns = ["URL"] + (["Quantity"] if show_qty else [])
    rows = [[url, qty] for url, qty in data] if show_qty else zip(list(zip(*data))[0])
    print_table(columns, rows)


def get_qty():
    while True:
        qty = input("Quantity (optional): ")

        if qty.strip() == "" or qty == "inf":
            return "inf"

        qty = validate_num(qty, int)
        if qty is None or qty < 1:
            Colors.print(
                "Invalid input for quantity. Please enter an integer greater than or equal to 1.",
                properties=["fail"],
            )
        else:
            return qty


class QtyManager:
    def __init__(self, qty):
        self.qty = qty

    def get(self):
        return self.qty

    def decrement(self):
        self.qty -= 1


def add_url():
    new_url = input("URL to add: ")
    if new_url.strip() == "":
        print("Aborted.")
        return

    urls = _read()
    qty = get_qty()
    urls[new_url] = qty
    _save(urls)
    Colors.print(
        f"Successfully added {new_url}{'' if qty == 'inf' else f' with a quantity of {qty}'}!",
        properties=["success"],
    )


def add_url_group():
    url_group = []
    i = 1

    while True:
        new_url = input("URL to add: ")

        if new_url.strip() == "":
            if i == 1:
                print("Aborted.")
                break
            else:
                continue

        url_group.append(new_url)

        if i >= 2 and not yes_or_no("Would you like to add another URL (y/n): "):
            break

        i += 1

    urls = _read()
    qty = get_qty()
    urls["\n".join(url_group)] = qty
    _save(urls)
    Colors.print(
        f"Successfully added a URL group with {len(url_group)} URLs{'' if qty == 'inf' else f' and a quantity of {qty} for the group'}!",
        properties=["success"],
    )


def remove_url():
    urls = _read()
    ids = range(1, len(urls) + 1)
    rows = list(zip(ids, urls.keys()))
    print_table(["ID", "Active URLs"], rows, justifications=["center", "left"])

    while True:
        url_id = input("URL ID to remove: ").strip()

        if url_id == "":
            continue

        url_id = validate_num(url_id, int)
        if url_id is None or url_id < ids[0] or url_id > ids[-1]:
            Colors.print(
                f"Please enter valid URL ID between {ids[0]}-{ids[-1]}. Do not enter the URL itself.",
                properties=["fail"],
            )
        else:
            break

    selected_url = list(urls.keys())[url_id - 1]
    del urls[selected_url]
    _save(urls)

    comma_separated_selection = selected_url.replace("\n", ", ")
    Colors.print(
        f"Successfully removed: {comma_separated_selection}", properties=["success"]
    )


def get_url_titles():
    flattened_urls = [
        url
        for url_group, _ in get_url_data()
        for url in (url_group if type(url_group) is list else [url_group])
    ]

    session = Session()
    session.headers.update({"user-agent": get_user_agent()})
    retry = Retry(
        connect=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    for url in flattened_urls:
        try:
            response = session.get(url, timeout=10)
        except RequestException as e:
            Colors.print(e, properties=["fail", "bold"])
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        raw_title = soup.find("div", class_="sku-title")
        if raw_title is None:
            Colors.print(
                f"Unable to find title for {url}.", properties=["fail", "bold"]
            )
            continue
        title = raw_title.get_text().strip()

        in_stock = soup.find(
            "button",
            {"data-button-state": "ADD_TO_CART"},
        )
        if in_stock:
            Colors.warn(f"{title} is already in stock.")

        yield title

    session.close()


def test_urls():
    with loading("Testing URLs"):
        for title in get_url_titles():
            Colors.print(f"Confirmed {title}!", properties=["success"])


def clear_urls():
    _save({})
    Colors.print("Successfully removed all URLs!", properties=["success"])
