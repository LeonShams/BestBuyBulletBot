Prerequisites
=============

.. role:: bash(code)
   :language: bash

#. A Best Buy account with your location and payment information already set in advance.

    The only information the bot will fill out during checkout is your login credentials (email and password) and the CVV of the card used when setting up your payment information on Best Buy (PayPal is currently not supported). All other information that may be required during checkout must be filled out beforehand.

    * A shipping address can be set at https://www.bestbuy.com/profile/c/address/shipping/add.

    * Your payment methods can be viewed and modified at https://www.bestbuy.com/profile/c/billinginfo/cc.

#. Python 3.6 or newer

    3B Bot is written in Python so if it is not already installed on your computer please install it from https://www.python.org/downloads/.

    .. note::

        **On Windows make sure to tick the "Add Python to PATH" checkbox during the installation process.** On MacOS this is done automatically.

        .. image:: https://lh6.googleusercontent.com/Xirse0uDfZCQaHnIAa7UCd1IRr5_hnFgv8qDUEkT98ENyQ7E5I8R8nLbWmYMl3g1blhUCooAhJsZnKDmjQqeqfyUZnbVaHDOZY7qX7sW6Ui8ZdTjm0fzkwoZwV0xbfjaW3i9bVeg

    |

    Feel free to install whichever version of Python you would like so long as it is 3.6 or greater. To check your version of the currently installed Python run the following in your shell.

    For MacOS:

    .. code-block:: bash

        python3 --version

    For Windows:

    .. code-block:: bash

        python --version

    If your version is less than 3.6 or you get the message :bash:`python is not recognized as an internal or external command` then install Python from the link above.

#. A supported browser

    3B Bot currently only supports `Chrome <https://www.google.com/chrome/>`_ and `Firefox <https://www.mozilla.org/en-US/firefox/new/>`_. We recommend using the Firefox browser for it's superior performance during tracking.

    .. note::

        Only the regular edition of each browser is supported, so if you have Firefox Developer Edition or Chrome Dev you would need to install the regular edition on top of your current installation.

    .. image:: assets/firefox.png
