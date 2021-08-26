import builtins
import os
import signal
import sys
import time
from multiprocessing import Pool
from multiprocessing.managers import BaseManager
from multiprocessing.pool import ThreadPool
from threading import Event, Lock

import psutil
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util.retry import Retry
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from best_buy_bullet_bot.audio import sound_effects
from best_buy_bullet_bot.browser import purchase
from best_buy_bullet_bot.data import user_data
from best_buy_bullet_bot.data.setting_utils import (
    DRIVER_NAMES,
    SOUND_MODES,
    MoneyManager,
    get_settings,
)
from best_buy_bullet_bot.data.url_utils import QtyManager
from best_buy_bullet_bot.tracker.progress_bar import IndefeniteProgressBar
from best_buy_bullet_bot.utils import Colors

WINDOWS = sys.platform == "win32"
SETTINGS = get_settings()
SOUND_MODE = SETTINGS["sound mode"]
AUTO_CHECKOUT = SETTINGS["auto checkout"]
BROWSER_NAME = SETTINGS["browser"]
DRIVER_WRAPPER = DRIVER_NAMES[BROWSER_NAME]
NUM_THREADS = SETTINGS["threads"]


class TwoWayPause:
    def __init__(self):
        self.play = Event()
        self.play.set()
        self.pause = Event()

    def is_set(self):
        return self.pause.is_set()

    def set(self):
        self.play.clear()
        self.pause.set()

    def clear(self):
        self.pause.clear()
        self.play.set()

    def wait(self):
        self.pause.wait()

    def wait_inverse(self):
        self.play.wait()


# The following two classes are needed to use magic methods with `BaseManager`
class NoMagicLock:
    def __init__(self):
        self.lock = Lock()

    def enter(self, *args, **kwargs):
        self.lock.__enter__(*args, **kwargs)

    def exit(self, *args, **kwargs):
        self.lock.__exit__(*args, **kwargs)


class NormalLock:
    def __init__(self, no_magic_lock):
        self.lock = no_magic_lock

    def __enter__(self, *args, **kwargs):
        self.lock.enter(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        self.lock.exit(*args, **kwargs)


BaseManager.register("ThreadLock", NoMagicLock)
BaseManager.register("QtyManager", QtyManager)
BaseManager.register("IndefeniteProgressBar", IndefeniteProgressBar)
BaseManager.register("PauseEvent", TwoWayPause)
BaseManager.register("MoneyManager", MoneyManager)


STOCK = False


def track(
    title,
    url,
    qty,
    headless,
    login_cookies,
    password,
    cvv,
    thread_lock,
    paused,
    pbar,
    pred_price,
    money_manager,
    headers,
):
    builtins.print = pbar.print
    if not AUTO_CHECKOUT:
        headers["referer"] = url

    thread_lock = NormalLock(thread_lock)

    with ThreadPool(NUM_THREADS) as pool:
        pool.starmap_async(
            run,
            [
                [
                    title,
                    url,
                    qty,
                    login_cookies,
                    thread_lock,
                    paused,
                    pbar,
                    pred_price,
                    money_manager,
                    headers,
                ]
                for _ in range(NUM_THREADS)
            ],
        )

        await_checkout(
            title,
            url,
            qty,
            headless,
            login_cookies,
            password,
            cvv,
            paused,
            pred_price,
            money_manager,
        )


def await_checkout(
    title,
    url,
    qty,
    headless,
    login_cookies,
    password,
    cvv,
    paused,
    pred_price,
    money_manager,
):
    global STOCK

    while True:
        paused.wait()

        if STOCK:
            if not money_manager.check_funds(pred_price) or not qty.get():
                paused.clear()

                if SOUND_MODE == SOUND_MODES[2]:
                    sound_effects.stop()

                Colors.print(
                    f'All requested "{title}" were purchased.'
                    if money_manager.check_funds(pred_price)
                    else f"With only ${money_manager.get_funds():,.2f} you cannot afford {title}.",
                    "It will no longer be tracked to conserve resources.\n",
                    properties=["warning"],
                )
                return

            current_time = time.strftime("%H:%M:%S", time.localtime())
            Colors.print(
                f'\n{current_time} - "{title}" - {url}\n',
                properties=["bold"],
            )

            # Plays a sound
            if SOUND_MODE == SOUND_MODES[1]:
                sound_effects.play()
            elif SOUND_MODE == SOUND_MODES[2]:
                sound_effects.start()

            if AUTO_CHECKOUT:
                try:
                    while money_manager.check_funds(pred_price) and qty.get():
                        if purchase(
                            url,
                            login_cookies,
                            headless,
                            *STOCK,  # `headless_driver` and `headless_wait`
                            title,
                            password,
                            cvv,
                            money_manager,
                        ):
                            qty.decrement()
                        else:
                            break
                except Exception as e:
                    Colors.print(
                        f"CHECKOUT ERROR: {e}",
                    )

            STOCK = False
            paused.clear()
        else:
            paused.wait_inverse()


def run(
    title,
    url,
    qty,
    login_cookies,
    thread_lock,
    paused,
    pbar,
    pred_price,
    money_manager,
    headers,
):
    global STOCK

    stop_tracker = False

    if AUTO_CHECKOUT:
        options = DRIVER_WRAPPER.options()
        options.page_load_strategy = "none"
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--headless")

        # Suppress "DevTools listening on ws:..." message
        if BROWSER_NAME == "chrome":
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Create the browser window
        driver = DRIVER_WRAPPER.driver(
            executable_path=DRIVER_WRAPPER.manager().install(), options=options
        )

        # Login to the browser by setting the cookies
        driver.get(url)
        for cookie in login_cookies:
            driver.add_cookie(cookie)

        wait = WebDriverWait(driver, 120)
        button_locator = EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                ".fulfillment-add-to-cart-button > div > div > button",
            )
        )

        # Confirm that we have a stable connection and that Best Buy hasn't made any
        # changes to their website that would break out locator
        try:
            btn = wait.until(button_locator)
        except TimeoutException:
            Colors.print(
                f"Unable to connect to {title}. Closing tracker.",
                properties=["fail"],
            )
            stop_tracker = True
    else:
        session = Session()
        session.headers.update(headers)
        retry = Retry(
            connect=3,
            backoff_factor=0.25,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

    connection_status = True
    available = False
    prev_available = False

    # Track item so long as we have sufficient funds and haven't bought the item too many times
    while not stop_tracker and (
        not AUTO_CHECKOUT or (money_manager.check_funds(pred_price) and qty.get())
    ):
        # Stop trackers to conserve resources during the auto checkout process
        if paused.is_set():
            paused.wait_inverse()
            continue

        if AUTO_CHECKOUT:
            driver.get(url)

            try:
                # Wait until old page has unloaded
                wait.until(EC.staleness_of(btn))

                if paused.is_set():
                    # Stop page load (page will reload when tracker restarts)
                    driver.execute_script("window.stop();")
                    continue

                # Wait until the add-to-cart button is present on the new page
                btn = wait.until(button_locator)

            # Inform the user if an error occurs while trying to locate the add-to-cart button
            except TimeoutException:
                if connection_status:
                    start_time = time.time()
                    Colors.print(
                        f"{title} tracker has lost connection.\n",
                        properties=["fail"],
                    )
                    connection_status = False
                continue

            # Check if it is an add-to-cart button
            available = btn.get_attribute("data-button-state") == "ADD_TO_CART"

        else:
            try:
                # Make a get request
                response = session.get(url, timeout=10)
                response.raise_for_status()

            except RequestException as e:
                # Inform the user if an error occurs while trying to make a get request
                if connection_status:
                    start_time = time.time()
                    Colors.print(
                        f"Unable to establish a connection to {title} remote endpoint.",
                        properties=["fail"],
                    )
                    print(e, "\n")
                    connection_status = False
                continue

            if paused.is_set():
                continue

            # Look for add-to-cart button
            soup = BeautifulSoup(response.text, "html.parser")
            available = (
                soup.find(
                    "button",
                    {"data-button-state": "ADD_TO_CART"},
                )
                is not None
            )

        pbar.update()

        # If we reconnected, inform the user
        if not connection_status:
            Colors.print(
                f"{title} tracker has successfully reconnected!",
                properties=["success"],
            )
            print(f"Downtime: {time.time()-start_time:.2f} seconds \n")
            connection_status = True

        # If the item is in stock
        if available:
            # Unlock the checkout process if it hasn't been already
            with thread_lock:
                if paused.is_set():
                    continue

                if AUTO_CHECKOUT:
                    if not STOCK:
                        STOCK = (driver, wait)
                else:
                    STOCK = True
                paused.set()

        # If item went back to being out of stock
        elif prev_available != available:
            if SOUND_MODE == SOUND_MODES[2]:
                sound_effects.stop()

        prev_available = available

    # Stop the auto checkout function
    if STOCK is not True:
        STOCK = True
        paused.set()

    if AUTO_CHECKOUT:
        driver.close()
    else:
        session.close()


def set_priority(high_priority):
    p = psutil.Process(os.getpid())

    """
    EASTER EGG: Thank you for reading the source code!
    To run the bot with a higher priority level and achieve better performance complete the following.

    If using Firefox, complete the following before moving on to the next step:
    WINDOWS: Open a Command Prompt window with "Run as administrator" https://www.educative.io/edpresso/how-to-run-cmd-as-an-administrator
    MAC: Enter the command `su` in your terminal to gain root privileges. Beware your settings may be different in the root session, but you can always return to a normal session with the `exit` command.

    Then regardless of your browser:
    Run `3b-bot --fast` in your shell.
    """
    # Windows: REALTIME_PRIORITY_CLASS, HIGH_PRIORITY_CLASS, ABOVE_NORMAL_PRIORITY_CLASS, NORMAL_PRIORITY_CLASS, BELOW_NORMAL_PRIORITY_CLASS, IDLE_PRIORITY_CLASS
    # MacOS: -20 is highest priority while 20 is lowest priority
    # Lower priorities are used here so other things can still be done on the computer while the bot is running
    priority = (
        (psutil.HIGH_PRIORITY_CLASS if WINDOWS else -10)
        if high_priority
        else (psutil.BELOW_NORMAL_PRIORITY_CLASS if WINDOWS else 10)
    )
    p.nice(priority)


def start(fast=False, headless=False, verify_account=False, skip_verification=False):
    from elevate import elevate

    from best_buy_bullet_bot.browser import browser_startup, get_user_agent
    from best_buy_bullet_bot.data import close_data, url_utils
    from best_buy_bullet_bot.utils import loading, warnings_suppressed, yes_or_no

    """
    EASTER EGG: Thank you for reading the source code!
    To run the bot with a higher priority level and achieve better performance complete the following.

    If using Firefox, complete the following before moving on to the next step:
    WINDOWS: Open a Command Prompt window with "Run as administrator" https://www.educative.io/edpresso/how-to-run-cmd-as-an-administrator
    MAC: Enter the command `su` in your terminal to gain root privileges. Beware your settings may be different in the root session, but you can always return to a normal session with the `exit` command.

    Then regardless of your browser:
    Run `3b-bot --fast` in your shell.
    """

    # If we don't have admin privilidges try to elevate permissions
    if fast and hasattr(os, "getuid") and os.getuid() != 0:
        print("Elevating permissions to run in fast mode.")
        elevate(graphical=False)

    def kill_all(*args, **kwargs):
        if not WINDOWS:
            # Delete the temp file
            close_data()

        # Forcefully close everything
        os.system(
            f"taskkill /F /im {psutil.Process(os.getpid()).name()}"
        ) if WINDOWS else os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)

    def clean_kill(*args, **kwargs):
        # Suppress error messages created as a result of termination
        # Selenium will often print long error messages during termination
        sys.stderr = open(os.devnull, "w")

        # Close the pbar and kill everything if the process pool has been created
        if "pbar" in locals():
            pbar.close()
            print()
            kill_all()  # Inelegant but fast

        # Otherwise we can exit the traditional way
        else:
            print()
            sys.exit(0)

    # Use custom functions to exit properly
    for sig in [signal.SIGINT, signal.SIGBREAK if WINDOWS else signal.SIGQUIT]:
        signal.signal(sig, clean_kill)
    signal.signal(signal.SIGTERM, kill_all)

    print(
        """
 .d8888b.  888888b.        888888b.            888
d88P  Y88b 888  "88b       888  "88b           888
     .d88P 888  .88P       888  .88P           888
    8888"  8888888K.       8888888K.   .d88b.  888888
     "Y8b. 888  "Y88b      888  "Y88b d88""88b 888
888    888 888    888      888    888 888  888 888
Y88b  d88P 888   d88P      888   d88P Y88..88P Y88b.
 "Y8888P"  8888888P"       8888888P"   "Y88P"   "Y888

"""
    )

    # Check if a flag has been passed to suppress warnings
    suppress_warnings = warnings_suppressed()

    raw_urls = url_utils.get_url_data()
    if not len(raw_urls):
        print()
        Colors.warn("No URLs have been set to be tracked.")
        if not suppress_warnings:
            if yes_or_no("Would you like to set some URLs for tracking (y/n): "):
                while True:
                    url_utils.add_url()
                    if not yes_or_no("Do you want to add another url (y/n): "):
                        break
                raw_urls = url_utils.get_url_data()

        if not len(raw_urls):
            Colors.print(
                "Not enough URLs for tracking.",
                "Please add at least 1 URL.",
                "URLs can be added with `3b-bot add-url`.",
                properties=["fail", "bold"],
            )
            sys.exit(1)

    print("Tracking the following URLs.")
    url_utils.view_urls(AUTO_CHECKOUT)

    manager = BaseManager()
    manager.start()

    money_manager = manager.MoneyManager()
    if AUTO_CHECKOUT:
        print(f"Current funds: ${money_manager.get_funds():,.2f}")
    print()

    # Get URLs and a quantity object for each URL
    urls, qtys = [], []
    for url_group, raw_qty in raw_urls:
        int_qty = -1 if raw_qty == "inf" else raw_qty

        # Create a shared qty manager between URLs for URL groups
        qty = manager.QtyManager(int_qty) if len(url_group) > 1 else QtyManager(int_qty)

        urls += url_group
        qtys += [qty] * len(url_group)

    with loading("Checking URLs"):
        titles = list(url_utils.get_url_titles())

    if len(titles) < len(urls):
        sys.exit(1)
    elif len(titles) > len(urls):
        Colors.print(
            "Something went wrong!",
            "Please report the issue to https://github.com/LeonShams/BestBuyBulletBot/issues.",
            "Feel free to copy and paste the following when opening an issue.",
            properties=["fail", "bold"],
        )
        print(
            "ERROR ENCOUNTERED DURING EXECUTION: More titles than URLs!",
            f"Raw URLs: {raw_urls}",
            f"URLs: {urls}",
            f"Titles: {titles}",
            sep="\n",
        )
        sys.exit(1)

    if AUTO_CHECKOUT:
        email, password, cvv = user_data.get_creds()
        if not (email or password or cvv):
            Colors.warn(
                "\nCheckout credentials have not been set. Run `3b-bot set-creds` to add the necessary information."
            )

            if not suppress_warnings:
                if yes_or_no("Would you like to set your checkout credentials (y/n): "):
                    user_data.set_creds()
                    email, password, cvv = user_data.get_creds()

        print()
        login_cookies_list, predicted_prices = browser_startup(
            headless, email, password, urls, verify_account, skip_verification
        )
        headers = {}
    else:
        email, password, cvv = "", "", ""
        login_cookies_list, predicted_prices = ((None for _ in urls) for i in range(2))

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-origin",
            "user-agent": get_user_agent(),
        }

    Colors.print("Availability tracking has started!", properties=["success"])
    if fast:
        Colors.print("Fast tracking enabled!", properties=["blue"])
    print()

    # Create remaining shared objects
    thread_lock = manager.ThreadLock()
    paused = manager.PauseEvent()
    pbar = manager.IndefeniteProgressBar()

    # Start process for each URL
    with Pool(len(urls), set_priority, [fast]) as p:
        p.starmap(
            track,
            [
                [
                    title,
                    url,
                    qty,
                    headless,
                    login_cookies,
                    password,
                    cvv,
                    thread_lock,
                    paused,
                    pbar,
                    pred_price,
                    money_manager,
                    headers,
                ]
                for title, url, qty, login_cookies, pred_price in zip(
                    titles, urls, qtys, login_cookies_list, predicted_prices
                )
            ],
        )

    pbar.close()
    print("\nAll processes have finished.")
