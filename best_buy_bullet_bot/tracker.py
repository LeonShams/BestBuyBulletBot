import os
import signal
import sys
import time
from datetime import datetime
from multiprocessing import Pool, current_process
from multiprocessing.managers import BaseManager
from multiprocessing.pool import ThreadPool
from threading import Timer

import psutil
import pytz
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from best_buy_bullet_bot.auto_checkout import purchase
from best_buy_bullet_bot.data import user_data
from best_buy_bullet_bot.data.setting_utils import (
    SOUND_MODES,
    MoneyManager,
    get_settings,
)
from best_buy_bullet_bot.utils import (
    IndefeniteProgressBar,
    TwoWayPause,
    bcolors,
    yes_or_no,
)

BaseManager.register("IndefeniteProgressBar", IndefeniteProgressBar)
BaseManager.register("PauseEvent", TwoWayPause)
BaseManager.register("MoneyManager", MoneyManager)

WINDOWS = sys.platform == "win32"
BREAK_SIGNALS = [signal.SIGINT, signal.SIGBREAK if WINDOWS else signal.SIGQUIT]
RUNNING = True
settings = get_settings()
NUM_THREADS = settings["Speed"]
SOUND_MODE = settings["Sound Mode"]
AUTO_CHECKOUT = settings["Auto Checkout"]


def safe_exit(*args, **kwargs):
    from best_buy_bullet_bot.audio import sound_effects

    global RUNNING

    if not timer.is_alive() and not timer.finished.is_set():
        timer.start()  # In case anything goes wrong while exiting
    else:
        timer.function()

    print(f"Attempting safe exit for {current_process()}")
    RUNNING = False
    sound_effects.destroy(WINDOWS)


def kill_all(*args, **kwargs):
    os.system(
        f"taskkill /F /im {psutil.Process(os.getppid()).name()}"
    ) if WINDOWS else os.killpg(os.getpgid(os.getppid()), signal.SIGKILL)


timer = Timer(10, kill_all)
timer.daemon = True


TITLES = [None] * NUM_THREADS
IDX_SET = None
QTY = None


def track(
    url, qty, login_cookies, cvv, paused, pbar, pred_price, money_manager, headers
):
    for sig in BREAK_SIGNALS:
        signal.signal(sig, safe_exit)
    signal.signal(signal.SIGTERM, kill_all)

    global QTY
    QTY = -1 if qty == "inf" else qty

    headers["referer"] = url

    pool = ThreadPool(NUM_THREADS)
    pool.starmap_async(
        run,
        [
            [i, url, paused, pbar, pred_price, money_manager, headers]
            for i in range(NUM_THREADS)
        ],
    )

    await_checkout(url, login_cookies, cvv, paused, pred_price, money_manager)
    pool.close()
    pool.join()

    if timer.is_alive():
        timer.cancel()
    if timer.finished.is_set():
        timer.join()


def await_checkout(
    url, login_cookies, cvv, paused, pred_price, money_manager, **kwargs
):
    from best_buy_bullet_bot.audio import sound_effects

    global TITLES
    global IDX_SET

    try:
        paused.wait()
    except OSError:
        return
    if paused.is_terminated():
        return

    if IDX_SET != None:
        if IDX_SET == -1:
            paused.clear()
            bcolors.print(
                f"All requested {url} were purchased."
                if money_manager.check_funds(pred_price)
                else f"With only ${money_manager.get_funds():,.2f} you cannot afford {url}.",
                "It will no longer be tracked to conserve resources.",
                properties=["warning"],
            )
            sound_effects.destroy(WINDOWS)
            return

        title = TITLES[IDX_SET]
        tz_LA = pytz.timezone("America/Los_Angeles")
        datetime_LA = datetime.now(tz_LA)
        current_time = datetime_LA.strftime("%H:%M:%S")
        bcolors.print(
            f'\n\n{current_time} - "{title[:20] + "..." if len(title) > 20 else ""}" - {url}\n\n',
            properties=["bold"],
        )

        # Plays a sound
        if SOUND_MODE == SOUND_MODES[1]:
            sound_effects.play_sound()
        elif SOUND_MODE == SOUND_MODES[2]:
            sound_effects.start_sound()

        if AUTO_CHECKOUT:
            try:
                global QTY
                while money_manager.check_funds(pred_price) and QTY:
                    if purchase(url, login_cookies, cvv, money_manager):
                        QTY -= 1
                    else:
                        break
            except:
                pass

        TITLES[IDX_SET] = None
        IDX_SET = None

        paused.clear()
    else:
        try:
            paused.wait_inverse()
        except OSError:
            return

    await_checkout(**locals())


def run(idx, url, paused, pbar, pred_price, money_manager, headers):
    global TITLES
    global IDX_SET

    session = Session()
    session.timeout = 5
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

    available = False
    prev_available = False
    connection_status = True

    while RUNNING:
        if paused.is_set():
            if paused.is_terminated():
                break
            paused.wait_inverse()

        # Check if we have enough money to make the purchase
        if AUTO_CHECKOUT and (not money_manager.check_funds(pred_price) or not QTY):
            pause = IDX_SET == None
            IDX_SET = -1
            if pause:
                paused.set()
            break

        # Get page data
        try:
            response = session.get(url)
            response.raise_for_status()
            pbar.update()

            if not connection_status:
                bcolors.print(
                    "\nSuccessfully reconnected to remote endpoint!",
                    properties=["success", "bold"],
                )
                print(f"Downtime: {round(time.time()-start_time, 2)} seconds \n")
                connection_status = True

        except Exception as e:
            if connection_status:
                start_time = time.time()
                bcolors.print(
                    "\nUnable to establish a connection with remote endpoint.",
                    properties=["fail", "bold"],
                )
                print(e, "\n")
                connection_status = False
            continue

        # Check if item is available
        soup = BeautifulSoup(response.text, "html.parser")
        available = (
            soup.find(
                "button",
                class_="btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button",
            )
            is not None
        )

        # If item comes back in stock
        if prev_available != available:
            if available:
                title = soup.find_all("div", class_="sku-title")[0].get_text().strip()
                IDX_SET = idx
                TITLES[idx] = title
                paused.set()
            else:
                from best_buy_bullet_bot.audio import sound_effects

                if SOUND_MODE == SOUND_MODES[2]:
                    sound_effects.stop_sound()

        prev_available = available

    session.close()
    if IDX_SET != -1:
        paused.set(terminate=True)


def start():
    import warnings

    from best_buy_bullet_bot.auto_checkout import get_user_agent, login
    from best_buy_bullet_bot.data import url_utils

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

    def pretty_warning(msg, *args, **kwargs):
        return bcolors.str(f"WARNING: {msg}\n", properties=["warning"])

    # Warnings are used because they can easily be suppressed with `-W ignore`
    warnings.formatwarning = pretty_warning
    supress_warning = "ignore" in sys.warnoptions

    print("Tracking the following urls. To view the full urls run `3b-bot view-urls`.")
    url_utils.view_urls(AUTO_CHECKOUT, max_url_chars=55)
    raw_urls = url_utils.get_url_data()

    if not len(raw_urls):
        print()
        warnings.warn("No URLS have been set to be tracked.")
        if not supress_warning:
            if yes_or_no("Would you like to set some URLS for tracking (y/n): "):
                while True:
                    url_utils.add_url()
                    if not yes_or_no("Do you want to add another url (y/n): "):
                        break
                raw_urls = url_utils.get_url_data()

        if not len(raw_urls):
            bcolors.print(
                "Not enough URLS for tracking.",
                "Please add at least 1 URL.",
                "URLS can be added with `3b-bot add-url`.",
                properties=["fail"],
            )
            sys.exit(0)

    urls, quantities = list(zip(*raw_urls))
    print()

    if AUTO_CHECKOUT:
        email, password, cvv = user_data.get_creds()
        if not (email or password or cvv):
            warnings.warn(
                "Checkout credentials have not been set. Run `3b-bot set-creds` to add the necessary information."
            )

            if not supress_warning:
                if yes_or_no("Would you like to set your checkout credentials (y/n): "):
                    user_data.set_creds()

        print("\nLogging in...")
        login_cookies_list, predicted_prices, user_agent = login(email, password, urls)
        print("Successfully logged into account!")
    else:
        email, password, cvv = [""] * 3
        login_cookies_list, predicted_prices = [[None] * len(urls)] * 2
        user_agent = get_user_agent()

    bcolors.print(
        "\nAvailablility tracking has started!", properties=["success", "bold"]
    )

    def notify_procs(*args, **kwargs):
        if len(psutil.Process().children(recursive=True)):
            print("\n")
        else:
            sys.exit(0)

    def kill_all(*args, **kwargs):
        os.system(
            f"taskkill /F /im {psutil.Process(os.getpid()).name()}"
        ) if WINDOWS else os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)

    for sig in BREAK_SIGNALS:
        signal.signal(sig, notify_procs)
    signal.signal(signal.SIGTERM, kill_all)

    def limit_cpu():
        p = psutil.Process(os.getpid())

        # Windows: REALTIME_PRIORITY_CLASS, HIGH_PRIORITY_CLASS, ABOVE_NORMAL_PRIORITY_CLASS, NORMAL_PRIORITY_CLASS, BELOW_NORMAL_PRIORITY_CLASS, IDLE_PRIORITY_CLASS
        # MacOS: -20 is highest priority while 20 is lowest priority
        # Lower priorities are used here so other things can still be done on the computer while the bot is running
        priority = psutil.BELOW_NORMAL_PRIORITY_CLASS if WINDOWS else 10
        p.nice(priority)

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-origin",
        "user-agent": user_agent,
    }

    manager = BaseManager()
    manager.start()
    money_manager = manager.MoneyManager()

    if AUTO_CHECKOUT:
        print(f"Current funds: ${money_manager.get_funds():,.2f}")
    print()

    paused = manager.PauseEvent()
    pbar = manager.IndefeniteProgressBar()

    pool = Pool(len(urls), limit_cpu())
    pool.starmap(
        track,
        [
            [
                url,
                qty,
                login_cookies,
                cvv,
                paused,
                pbar,
                pred_price,
                money_manager,
                headers,
            ]
            for url, qty, login_cookies, pred_price in zip(
                urls, quantities, login_cookies_list, predicted_prices
            )
        ],
    )
    pool.close()
    pool.join()
    pbar.close()

    bcolors.print("Successfully closed all processes!", properties=["success", "bold"])
