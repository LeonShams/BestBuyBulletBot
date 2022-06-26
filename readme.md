# Best Buy Bullet Bot (3B Bot)

Best Buy Bullet Bot, abbreviated to 3B Bot, is a stock checking bot with auto-checkout created to instantly purchase out-of-stock items on Best Buy once restocked. It was designed for speed with ultra-fast auto-checkout, as well as the ability to utilize all cores of your CPU with multiprocessing for optimal performance.

* Headless item stock tracking

* Multiprocessing and multithreading for best possible performance

* One-time login on startup

* Ultra-fast auto-checkout

* Encrypted local credentials storage

* Super easy setup and usage

Bear in mind that 3B Bot is currently not equipped to handle a queue and/or email verification during the checkout process. If either of these is present, the bot will wait for you to take over and will take control again once you are back on the traditional checkout track.

![3B Bot](https://raw.githubusercontent.com/LeonShams/BestBuyBulletBot/main/docs/source/assets/demo.svg)
<br>

## Prerequisites

1. **A Best Buy account with your location and payment information already set in advance.**

    The only information the bot will fill out during checkout is your login credentials (email and password) and the CVV of the card used when setting up your payment information on Best Buy (PayPal is currently not supported). All other information that may be required during checkout must be filled out beforehand.

2. **Python 3.6 or newer**

    3B Bot is written in Python so if it is not already installed on your computer please install it from <https://www.python.org/downloads/>.

    **On Windows make sure to tick the “Add Python to PATH” checkbox during the installation process.** On MacOS this is done automatically.

    Once installed, checking your Python version can be done with the following.

    For MacOS:

    ```bash
    python3 --version
    ```

    For Windows:

    ```bash
    python --version
    ```

    If your version is less than 3.6 or you get the message `python is not recognized as an internal or external command` then install python from the link above.

3. **A supported browser**

    3B Bot currently only supports [Chrome](https://www.google.com/chrome/) and [Firefox](https://www.mozilla.org/en-US/firefox/new/). We recommend using the Firefox browser for it's superior performance during tracking.

## Installation

Installing 3B Bot is as simple as running the following in your shell (Command Prompt for Windows and Terminal for MacOS)

For MacOS:

```bash
python3 -m pip install --upgrade 3b-bot
```

For Windows:

```bash
pip install --upgrade 3b-bot
```

## Usage

To start the bot just enter the following in your shell

```bash
3b-bot
```

**For more usage information check out our [documentation](https://bestbuybulletbot.readthedocs.io/en/latest/).**

## How does it work?

This is what 3B Bot does step by step at a high level

1. Get currently set URLs to track or prompt if none are set.

2. Using the requests library validate all URLs and get item names.

3. Open up a Google Chrome browser with selenium and perform the following.

    a. Navigate to the login page.

    b. If we have logged in previously we can use the saved cookies from the previous session to skip the log-in process. If not automatically fill out the username and password fields to log in.

    c. Make a get request to the Best Buy API to confirm that there are no items in the cart.

    d. If this is the first time using the bot check that a mailing address and payment information has been set.

    e. Go to each URL and collect the page cookies. This is done so that during checkout we can just apply the cookies for that URL instead of going through the entire login process.

4. Assign each URL to a core on the CPU.

5. Each core will start a specified number of threads.

6. Each thread will repeatedly check whether the "add to cart button" is available for its item.

7. When a thread notices that an item has come back in stock it will unlock its parent core and lock all other threads on every core to conserve CPU resources and WIFI.

8. The unlocked parent will print to the terminal that the item has come back in stock, play a sound, and attempt to automatically checkout the item with the following steps.

    a. With the driver that was used to track the item, click the add-to-cart button.

    b. Open up another browser window (this one is visible) and navigate to the item URL to set some cookies to login.

    c. Redirect to the checkout page.

    d. Enter the CVV for the card.

    e. Click "place order".

9. Once finished the parent will update its funds, the item quantity, and unlock all threads to resume stock tracking.

10. Sound will stop playing when the item is no longer in stock.

## Performance tips

The following are tips to achieve the best possible performance with 3B Bot.

* Use the same amount of URLs as cores on your CPU. You can create a URL group with the same URL repeated multiple times to increase the number of URLs you have and `3b-bot count-cores` can be used to see how many cores your CPU has.

* Use ethernet as opposed to WIFI for a stronger more stable connection.

* Adequately cool your computer to prevent thermal throttling.

* Tweak the number of threads per URL. This can be changed with the `3b-bot set-threads` command.

* If you plan to complete the checkout process yourself, disable auto-checkout in the settings for a significant performance improvement.

Overall, item stock tracking is a CPU and internet bound task, so at the end of the day the better your CPU and the stronger your internet the faster your tracking.
