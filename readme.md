# Best Buy Bullet Bot (3B Bot)

### :warning: Warning: Currently in beta! Not equipped to handle new Best Buy checkout process for Nvidia cards

3B Bot is a stock checking bot with auto-checkout created to instantly purchase out-of-stock items on Best Buy once restocked. It was designed for speed with ultra-fast auto-checkout, as well as the ability to check for item restock up to a hundred times a second by utilizing all cores of your CPU (multiprocessing).

* Headless item stock tracking (updates up to 100x a second)

* Multiprocessing and multithreading for best possible performance

* One time login on startup

* Ultra fast auto-checkout

* Encrypted local credentials storage

![3B Bot](https://drive.google.com/uc?export=view&id=1_Feew9--avxnnU8sYMUwYlaMv_OThBr8)

## Installation

Installing 3B Bot is as simple as

```bash
pip install 3b-bot
```

## Prerequisites

**To use 3B Bot you must already have Best Buy account with an address and payment informtion already set in advance.**

The only information the bot will fill out during autocheckout is your login credentials (email and password) and the cvv of the card used when setting up your payment information on Best Buy.

## Usage

To start the bot just enter the following in your shell

```bash
3b-bot
```

For more usage information check out our [wiki](https://github.com/LeonShams/BestBuyBulletBot/wiki).
