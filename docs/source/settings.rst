Settings
========

**Funds**

Funds signifiy the maximum amount of money the bot is permitted to spend and can be set using the :code:`set-funds` command. Make sure that your funds never exceed the amount of money on your card to prevent your card from getting declined during checkout. By default funds are set to $1,000.

**Tax**

Your state's tax rate is used to predict the price of an item so that we don't track items that exceed our funds. The tax rate can be set with the :code:`set-tax` command.

**Auto Checkout**

If auto checkout is enabled the bot will attempt to automatically complete the checkout process for you as fast as possible. If it gets stuck during checkout it will wait for up to 20 minutes for you to take over. If you take over within that timeframe the bot will take back control once it sees something that it knows how to handle.

Bear in mind that disabling auto checkout comes with some benefits as well: faster startup, no personal data needs to be stored, and most importantly MUCH faster tracking. Without auto checkout we can make get requests instead of having to refresh the page constantly. This is orders of magnitude faster and if you intend to do the checkout process yourself it is the way to go.

**Browser**

Choose which browser to use for tracking and auto checkout. This only applies if auto chekcout is enabled. Auto checkout can be toggled with the :code:`toggle-auto-checkout` command.

**Sound Mode**

When items come back in stock a sound will start playing to alert you of their availability. This parameter will specify whether you would like the sound to be completely disabled, to play once on restock, or play repeatedly until the item is no longer in stock.

**Threads**

Threads specify the number of trackers that should be started for each URL. Because it takes a while to get a response from Best Buy servers after making a get request multiple threads can be started so another thread can make a request while the other is waiting for a response.

Threads can be set with the :code:`set-threads` command, but be cautious as to not set this value too high or you might overwhelm you CPU and actually hurt your performance.

.. list-table::
   :widths: 50, 50
   :header-rows: 1

   * - 1 Thread
     - 3 Threads
   * - .. image:: https://files.realpython.com/media/IOBound.4810a888b457.png
     - .. image:: https://files.realpython.com/media/Threading.3eef48da829e.png

Image credit: https://realpython.com/python-concurrency/
