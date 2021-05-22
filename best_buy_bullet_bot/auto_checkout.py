import logging
import sys

import clipboard
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from best_buy_bullet_bot.data.setting_utils import get_settings
from best_buy_bullet_bot.utils import bcolors

logging.disable(logging.WARNING)
DRIVER_PATH = ChromeDriverManager().install()
settings = get_settings()

TAX = settings["Tax"]
MAC = sys.platform == "darwin"
USER_TAKEOVER = 120


def get_options(headless):
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.page_load_strategy = "none"
    if headless:
        options.add_argument("--headless")
    return options


DEFAULT_OPTIONS = get_options(settings["Headless"])


def get_user_agent():
    driver = webdriver.Chrome(DRIVER_PATH, options=get_options(True))
    user_agent = driver.execute_script("return navigator.userAgent")
    driver.quit()
    return user_agent


def money2float(money):
    return float(money[1:].replace(",", ""))


def fast_text(text):
    clipboard.copy(text)
    return (Keys.COMMAND if MAC else Keys.CONTROL) + "v"


def login(email, password, urls):
    driver = webdriver.Chrome(DRIVER_PATH, options=DEFAULT_OPTIONS)
    driver.get("https://www.bestbuy.com/identity/global/signin")

    user_agent = driver.execute_script("return navigator.userAgent")

    WebDriverWait(driver, USER_TAKEOVER).until(
        EC.visibility_of_element_located((By.ID, "fld-e"))
    ).send_keys(fast_text(email))
    driver.find_element_by_id("fld-p1").send_keys(fast_text(password))
    driver.find_element_by_id("ca-remember-me").click()
    driver.find_element_by_xpath(
        "/html/body/div[1]/div/section/main/div[2]/div[1]/div/div/div/div/form/div[4]/button"
    ).click()

    try:
        WebDriverWait(driver, USER_TAKEOVER).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".shop-search-bar, .cia-cancel")
            )
        )
    except TimeoutException:
        pass

    login_cookies_list = []
    predicted_prices = []

    for url in urls:
        driver.get(url)
        EC.presence_of_element_located
        predicted_price = (
            WebDriverWait(driver, USER_TAKEOVER)
            .until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        ".price-box > div > div > .priceView-hero-price.priceView-customer-price",
                    )
                )
            )
            .text
        ).split("\n")[0]

        predicted_prices.append(money2float(predicted_price) * (1 + TAX))
        login_cookies_list.append(driver.get_cookies())

    driver.quit()
    return login_cookies_list, predicted_prices, user_agent


def purchase(url, login_cookies, cvv, money_manager):
    driver = webdriver.Chrome(DRIVER_PATH, options=DEFAULT_OPTIONS)
    driver.get(url)

    for cookie in login_cookies:
        driver.add_cookie(cookie)

    WebDriverWait(driver, USER_TAKEOVER).until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                ".btn.btn-primary.btn-lg.btn-block.btn-leading-ficon.add-to-cart-button",
            )
        )
    ).click()

    driver.get("https://www.bestbuy.com/checkout/r/fulfillment")

    WebDriverWait(driver, USER_TAKEOVER).until(
        EC.visibility_of_element_located((By.ID, "credit-card-cvv"))
    ).send_keys(fast_text(cvv))

    grand_total = money2float(
        driver.find_element_by_css_selector(
            ".order-summary__total > .order-summary__price > .cash-money"
        ).text
    )
    if money_manager.check_funds(grand_total):
        driver.find_element_by_xpath(
            '//*[@id="checkoutApp"]/div[2]/div[1]/div[1]/main/div[2]/div[2]/div/div[5]/div[3]/div/button'
        ).click()
        money_manager.make_purchase(grand_total)
        bcolors.print(
            f"Successfully purchased {url}. The item was a grand total of ${grand_total:,.2f} leaving you with ${money_manager.get_funds():,.2f} of available funds.",
            properties=["success"],
        )
        return True
    else:
        bcolors.print(
            f"Insuffient funds to purchase {url} which costs a grand total of ${grand_total:,.2f} while you only have ${money_manager.get_funds():,.2f} of available funds.",
            properties=["fail"],
        )
    return False
