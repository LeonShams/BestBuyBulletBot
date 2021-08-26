URLs
====

The following commands can be used to view and modify the added URLs.

* :code:`view-urls` View list of tracked URLs.
* :code:`add-url` Add URL to tracking list.
* :code:`add-url-group` Add multiple URLs and set a quantity for all of them as a whole instead of individually.
* :code:`remove-url` Remove a URL or URL group from the list of tracked URLs.
* :code:`test-urls` Tests all URLs to confirm that they are trackable. This is also run automatically on startup.
* :code:`clear-urls` Remove all tracked URLs.

Even with a quantity greater than 1, items will be purchased one at a time to prevent one person from buying up all the stock. For example, if you had a quantity of 2, when the item comes back in stock a single unit will be purchased, then if the item is still in stock, it will purchase the second item separately before exiting.

**What is a URL group?**

A URL group allows multiple URLs to connect to a single quantity. For example, if you wanted to get **one** RTX 3060 TI but didn't care whether it was manufactured by ASUS or EVGA you could add the URL for each of the cards to a URL group and set a quantity of 1. The bot will purchase whichever one comes back in stock first, and once purchased will stop tracking both of them since you only wanted one graphics card.
