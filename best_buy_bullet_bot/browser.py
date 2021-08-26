import logging
import sys

import clipboard
import requests
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from best_buy_bullet_bot.data.browser_login import (
    cookies_available,
    load_cookies,
    save_cookies,
)
from best_buy_bullet_bot.data.setting_utils import (
    DRIVER_NAMES,
    change_browser,
    get_settings,
    is_installed,
    update_setting,
)
from best_buy_bullet_bot.utils import Colors, loading

SETTINGS = get_settings()
TAX = SETTINGS["tax"]
BROWSER_NAME = SETTINGS["browser"]
DRIVER_WRAPPER = DRIVER_NAMES[BROWSER_NAME]
MAC = sys.platform == "darwin"
USER_TAKEOVER = 20 * 60  # 20 min for user to takeover if the bot gets stuck

logging.disable(logging.WARNING)
try:
    DRIVER_PATH = DRIVER_WRAPPER.manager().install()
except ValueError:
    if not is_installed(SETTINGS["browser"]):
        Colors.print(
            f"{SETTINGS['browser'].title()} is not installed on your computer.",
            properties=["fail"],
        )
        change_browser()


def _get_options(headless):
    options = DRIVER_WRAPPER.options()
    options.page_load_strategy = "none"
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")

    if headless:
        options.add_argument("--headless")

    # Suppress "DevTools listening on ws:..." message
    if BROWSER_NAME == "chrome":
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

    return options


PREBUILT_OPTIONS = [_get_options(False), _get_options(True)]


def get_user_agent():
    driver = DRIVER_WRAPPER.driver(
        executable_path=DRIVER_PATH, options=PREBUILT_OPTIONS[True]
    )
    user_agent = driver.execute_script("return navigator.userAgent")
    driver.quit()
    return user_agent


def money2float(money):
    return float(money[1:].replace(",", ""))


def fast_text(text):
    clipboard.copy(text)
    return (Keys.COMMAND if MAC else Keys.CONTROL) + "v"


account_page_url = "https://www.bestbuy.com/site/customer/myaccount"
billing_url = "https://www.bestbuy.com/profile/c/billinginfo/cc"


def terminate(driver):
    driver.quit()
    sys.exit(1)


def _login(driver, wait, headless, email, password, cookies_set):
    branch = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#ca-remember-me, .shop-search-bar")
        )
    )

    if branch.get_attribute("class") == "shop-search-bar":
        # We are already logged in
        return

    # Click "Keep me signed in" button
    branch.click()

    if not cookies_set:
        # Fill in email box
        driver.find_element_by_id("fld-e").send_keys(fast_text(email))

    # Fill in password box
    driver.find_element_by_id("fld-p1").send_keys(fast_text(password))

    # Click the submit button
    driver.find_element_by_css_selector(
        ".btn.btn-secondary.btn-lg.btn-block.c-button-icon.c-button-icon-leading.cia-form__controls__submit"
    ).click()

    # Check for error or redirect
    branch = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                ".shop-search-bar, "  # We got redirected to the account page
                ".cia-cancel, "  # Skippable verification page
                ".c-alert.c-alert-level-error, "  # Error popup message
                "#fld-e-text, "  # Invalid email address
                "#fld-p1-text",  # Invalid password
            )
        )
    )

    # If we hit an error
    if branch.get_attribute(
        "class"
    ) == "c-alert c-alert-level-error" or branch.get_attribute("id") in [
        "fld-e-text",
        "fld-p1-text",
    ]:
        if headless:
            # If headless raise error
            Colors.print(
                "Incorrect login info. Please correct the username or password.",
                properties=["fail", "bold"],
            )
            terminate(driver)
        else:
            # If headful ask the user to take over
            Colors.print(
                "Unable to login automatically. Please correct your credentials or enter the information manually.",
                properties=["fail"],
            )
            branch = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".shop-search-bar, .cia-cancel")
                )
            )

    # If we hit a skippable verification page
    if "cia-cancel" in branch.get_attribute("class"):
        # Redirect to the "my account" page
        driver.get(account_page_url)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "shop-search-bar")))

    save_cookies(driver)


def check_cart(driver):
    with loading("Confirming cart is empty"):
        # Confirm that the cart is empty
        headers = {
            "Host": "www.bestbuy.com",
            "User-Agent": driver.execute_script("return navigator.userAgent"),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.bestbuy.com/site/customer/myaccount",
            "X-CLIENT-ID": "browse",
            "X-REQUEST-ID": "global-header-cart-count",
            "Connection": "keep-alive",
            "Cookie": driver.execute_script("return document.cookie"),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0",
        }

        # Make a get request to the Best Buy API to get the number of items in the cart
        response = requests.get(
            "https://www.bestbuy.com/basket/v1/basketCount", headers=headers
        )
        items = response.json()["count"]

        if items != 0:
            Colors.print(
                "Too many items in the cart. Please empty your cart before starting the bot.",
                properties=["fail", "bold"],
            )
            terminate(driver)


def perform_account_verification(driver, wait):
    with loading("Verifying account setup"):
        # Check that a shipping address has been set
        shipping_address = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div.account-setting-block-container:nth-child(1) > div:nth-child(2) > a:last-child",
                )
            )
        )
        if shipping_address.get_attribute("class") == "":
            Colors.print(
                "Shipping address has not been set. You can add a shipping address to \
                your account at https://www.bestbuy.com/profile/c/address/shipping/add.",
                properties=["fail", "bold"],
            )
            terminate(driver)

        # Confirm that a default payment method has been created
        driver.get(billing_url)
        payment_method_list = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".pf-credit-card-list__content-spacer > ul.pf-credit-card-list__credit-card-list",
                )
            )
        )

        if payment_method_list.size["height"] == 0:
            Colors.print(
                f"A default payment method has not been created. Please create one at {billing_url}.",
                properties=["fail", "bold"],
            )
            terminate(driver)

    Colors.print("Account has passed all checks!", properties=["success"])


def collect_item_cookies(driver, wait, urls):
    login_cookies_list = []
    predicted_prices = []
    price_element = None

    with loading("Collecting cookies for each URL"):
        for url in urls:
            driver.get(url)

            if price_element is not None:
                wait.until(EC.staleness_of(price_element))

            price_element = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        ".pricing-price > div > div > div > .priceView-hero-price.priceView-customer-price",
                    )
                )
            )
            item_price = price_element.text.split("\n")[0]

            predicted_prices.append(money2float(item_price) * (1 + TAX))
            login_cookies_list.append(driver.get_cookies())

    return login_cookies_list, predicted_prices


def _browser_startup(
    driver, headless, email, password, urls, verify_account, skip_verification
):
    wait = WebDriverWait(driver, USER_TAKEOVER)

    with loading("Logging in"):
        driver.get(account_page_url)
        # We will then get redirected to the sign in page

        # If we have logged in previously we can use the cookies from that session
        # to skip steps in the login process and prevent the system from detecting
        # a bunch of logins from the same account
        cookies_exist = cookies_available()
        if cookies_exist:
            if load_cookies(driver):
                driver.refresh()
            else:
                # An error occurred while adding the login cookies
                cookies_exist = False

        _login(driver, wait, headless, email, password, cookies_exist)

    check_cart(driver)

    if not skip_verification:
        if SETTINGS["account verification"] or verify_account:
            perform_account_verification(driver, wait)
            if not verify_account:
                print("This was a one time test and will not be performed again.\n")
            update_setting("account verification", False)

    item_cookies = collect_item_cookies(driver, wait, urls)

    driver.quit()
    return item_cookies


def browser_startup(headless, *args, **kwargs):
    driver = DRIVER_WRAPPER.driver(
        executable_path=DRIVER_PATH, options=PREBUILT_OPTIONS[headless]
    )

    try:
        return _browser_startup(driver, headless, *args, **kwargs)

    # Timed out while trying to locate element
    except TimeoutException:
        Colors.print(
            "Browser window has timed out. Closing bot.", properties=["fail", "bold"]
        )
        terminate(driver)

    # User has closed the browser window
    except NoSuchWindowException:
        terminate(driver)


def _purchase(
    driver,
    title,
    password,
    cvv,
    money_manager,
):
    # Go to the checkout page
    driver.get("https://www.bestbuy.com/checkout/r/fast-track")
    wait = WebDriverWait(driver, USER_TAKEOVER)

    # Get to the CVV page
    while True:
        branch = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#credit-card-cvv, "  # Place order page
                    ".button--continue > button.btn.btn-lg.btn-block.btn-secondary, "  # Continue to payment info page
                    ".checkout-buttons__checkout > .btn.btn-lg.btn-block.btn-primary",  # We got redirected to the cart
                )
            )
        )

        # If we got redirected to the cart
        if branch.get_attribute("class") == "btn btn-lg btn-block btn-primary":
            branch.click()
            branch = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "#credit-card-cvv, "  # Place order page
                        ".button--continue > button.btn.btn-lg.btn-block.btn-secondary, "  # Continue to place order page (page before place order page)
                        "#fld-p1",  # Sign in (only requires password)
                    )
                )
            )

            # If it wants to confirm our password
            if branch.get_attribute("class").strip() == "tb-input":
                branch.send_keys(fast_text(password))
                driver.find_element_by_css_selector(
                    ".btn.btn-secondary.btn-lg.btn-block.c-button-icon.c-button-icon-leading.cia-form__controls__submit"
                ).click()  # Click sign in button

                # We will loop back around and handle what comes next
            else:
                break
        else:
            break

    # Select the CVV text box
    if branch.get_attribute("class") == "btn btn-lg btn-block btn-secondary":
        branch.click()
        cvv_box = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "credit-card-cvv",
                )
            )
        )
    else:
        cvv_box = branch
    cvv_box.send_keys(fast_text(cvv))

    # Locate and parse the grand total text
    grand_total = money2float(
        driver.find_element_by_css_selector(
            ".order-summary__total > .order-summary__price > .cash-money"
        ).text
    )

    # Make sure we have sufficient funds for the purchase
    if money_manager.check_funds(grand_total):
        # Click place order button
        driver.find_element_by_css_selector(
            ".btn.btn-lg.btn-block.btn-primary, .btn.btn-lg.btn-block.btn-primary.button__fast-track"
        ).click()

        # Deduct grand total from available funds
        money_manager.make_purchase(grand_total)

        Colors.print(
            f"Successfully purchased {title}. The item was a grand total of ${grand_total:,.2f} leaving you with ${money_manager.get_funds():,.2f} of available funds.",
            properties=["success", "bold"],
        )
        return True
    else:
        Colors.print(
            f"Insuffient funds to purchase {title} which costs a grand total of ${grand_total:,.2f} while you only have ${money_manager.get_funds():,.2f} of available funds.",
            properties=["fail"],
        )
    return False


def purchase(
    url, login_cookies, headless, headless_driver, headless_wait, *args, **kwargs
):
    if not headless:
        # Create a new visible driver for the checkout process
        driver = DRIVER_WRAPPER.driver(
            executable_path=DRIVER_PATH, options=PREBUILT_OPTIONS[False]
        )
        driver.get(url)
        for cookie in login_cookies:
            driver.add_cookie(cookie)
    else:
        # Use the old headless driver so we don't have to create a new one
        driver = headless_driver

    # Have the existing headless tracker driver click the add-to-cart button
    headless_wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                ".fulfillment-add-to-cart-button > div > div > button",
            )
        )
    ).click()

    try:
        return _purchase(driver, *args, **kwargs)
    except TimeoutException:
        Colors.print(
            "3B Bot got stuck and nobody took over. Tracking will resume.",
            properties=["fail"],
        )
    except NoSuchWindowException:
        driver.quit()

    return False
