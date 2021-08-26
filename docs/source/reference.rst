Reference
=========

A list of all commands and flags can be viewied in the shell with the following command.

.. code-block:: bash

    3b-bot --help

Commands
--------

:code:`start`  Start tracking the currently set URLs. This is the default command.

:code:`view-urls` View list of tracked URLs.

:code:`add-url` Add URL to tracking list.

:code:`add-url-group` Add multiple URLs and set a quantity for all of them as a whole instead of individually.

:code:`remove-url` Remove a URL from the list of tracked URLs.

:code:`test-urls` Tests to make sure all URLs can be tracked. This is also run on startup.

:code:`clear-urls` Remove all tracked URLs.

:code:`view-settings` View current settings.

:code:`set-funds` Set how much money the bot is allowed to spend. Defaults to $1000.

:code:`set-tax` Set the sales tax rate for your state. Defaults to 9.5%.

:code:`toggle-auto-checkout` Enable/disable auto checkout.

:code:`change-browser` Pick the browser to be used during tracking and auto-checkout (only applies if auto-checkout is enabled). Firefox is the default and
recommended browser.

:code:`test-sound` Play sound sample.

:code:`set-sound-mode` Choose whether you want sound to be completely disabled, play once on item restock, or play repeatedly on item restock.

:code:`set-threads` Select the number of threads to allocate to tracking each URL.

:code:`count-cores` Print how many CPU cores you have and how many threads each core has.

:code:`reset-settings` Reset setting to the defaults.

:code:`view-creds` View your Best Buy login credentials (email, password, cvv).

:code:`set-creds` Set your Best Buy login credentials (email, password, cvv).

:code:`clear-creds` Reset your Best Buy login credentials (email, password, cvv). Also offers the option to reset your access password.

Flags
-----

Flags are options that can be passed alongside a command,with the exception of :code:`--help` and :code:`--version` which shouldn't be passed with any commands.

:code:`--version` Show 3B Bot version number.

:code:`--suppress-warnings` Suppress warnings.

:code:`--headless` Hide the browser during auto checkout.

:code:`--verify-account` Confirm that the account is setup properly (automatically performed on first run).

:code:`--skip-verification` Skip checks on first run that make sure account is setup properly.

:code:`--force-login` Force browser to go through traditional login process as opposed to using cookies to skip steps.
