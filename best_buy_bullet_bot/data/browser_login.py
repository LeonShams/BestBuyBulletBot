import json
import os
from json.decoder import JSONDecodeError

from best_buy_bullet_bot.data import SHARED_DIR

COOKIES_DIR = os.path.join(SHARED_DIR, "login_cookies.json")


def save_cookies(driver):
    with open(COOKIES_DIR, "w+") as f:
        json.dump(driver.get_cookies(), f)


def load_cookies(driver):
    try:
        with open(COOKIES_DIR) as f:
            for cookie in json.load(f):
                driver.add_cookie(cookie)
        return True

    # An error occurred while adding the cookies
    except AssertionError:
        # Delete previous cookies
        delete_cookies()
        return False


def cookies_available():
    file_exists = os.path.isfile(COOKIES_DIR)

    if file_exists:
        # Make sure file is JSON decodable
        try:
            with open(COOKIES_DIR) as f:
                json.load(f)
            return True

        except JSONDecodeError:
            delete_cookies()

    return False


def delete_cookies():
    os.remove(COOKIES_DIR)
