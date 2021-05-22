import os
import sys
from getpass import getpass
from threading import Timer

from best_buy_bullet_bot.utils import bcolors, yes_or_no
from keyring.errors import PasswordDeleteError
from keyrings.cryptfile.cryptfile import CryptFileKeyring

EMAIL_VAR = "BB_EMAIL"
PASS_VAR = "BB_PASS"
CVV_VAR = "BB_CVV"

SERVICE_ID = "3B_BOT"
KR = CryptFileKeyring()


def set_access_pass(access_pass):
    KR._keyring_key = access_pass


def authenticate():
    attempts = 0
    while True:
        try:
            KR.keyring_key
            return
        except ValueError:
            if str(KR._keyring_key).strip() == "":
                sys.exit()

            attempts += 1
            if attempts >= 3:
                print("Too many attempts, please try again later.")
                sys.exit()

            print("Sorry, try again.")
            KR._keyring_key = None


def _get_cred(name, default_value):
    cred = KR.get_password(SERVICE_ID, name)
    return cred if cred is not None else default_value


def get_creds(default_value=""):
    authenticate()
    return [_get_cred(var, default_value) for var in [EMAIL_VAR, PASS_VAR, CVV_VAR]]


def _get_input(prompt):
    while True:
        value = input(prompt)

        if yes_or_no("Continue (y/n): "):
            return value


def set_creds():
    authenticate()
    KR.set_password(SERVICE_ID, EMAIL_VAR, _get_input("Email: "))

    print()
    while True:
        password = getpass("Password: ")
        confirm_pass = getpass("Confirm password: ")
        if password == confirm_pass:
            break
        print("Passwords didn't match! Try again.")
    KR.set_password(SERVICE_ID, PASS_VAR, password)

    print()
    KR.set_password(SERVICE_ID, CVV_VAR, _get_input("CVV: "))
    bcolors.print("Sucessfully updated credentials!", properties=["success", "bold"])


def print_creds():
    email, password, cvv = get_creds(bcolors.str("EMPTY", ["fail", "bold"]))
    print("Email:", email)
    print("Password:", password)
    print("CVV:", cvv)


def _delete_cred(name):
    try:
        KR.delete_password(SERVICE_ID, name)
    except PasswordDeleteError:
        pass


def clear_creds():
    _delete_cred(EMAIL_VAR)
    _delete_cred(PASS_VAR)
    _delete_cred(CVV_VAR)
    bcolors.print("Credentials cleared!\n", properties=["success", "bold"])

    # Check if user wants to reset their password
    if yes_or_no("Would you like to reset your password (y/n): "):
        os.remove(KR.file_path)
        KR.keyring_key
