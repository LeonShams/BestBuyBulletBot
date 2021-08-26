Running the Bot
===============

.. role:: bash(code)
   :language: bash

To start the bot just enter the following in your shell

.. code-block:: bash

    3b-bot

.. note::

    The bot can be stopped at any time regardless of OS with ``ctrl+c``.

You will then be prompted to set some URLs to track. These URLs can be later modified with the commands :bash:`3b-bot add-url`, :bash:`3b-bot add-url-group`, :bash:`3b-bot remove-urls`, and :bash:`3b-bot clear-urls`.

Finally, you will be prompted to set a password for your encrypted keyring. The encrypted keyring is just the location that stores your Best Buy credentials (email, password, CVV). The keyring password is like a master password for all your credentials.

If you ever forget the password for your encrypted keyring, just clear your credentials with the following command and an opportunity will be granted to reset the password.

.. code-block:: bash

    3b-bot clear-creds

To view the list of commands run

.. code-block:: bash

    3b-bot --help
