from pathlib import Path

from setuptools import find_packages, setup

exec(
    compile(
        open("best_buy_bullet_bot/version.py").read(),
        "best_buy_bullet_bot/version.py",
        "exec",
    )
)

setup(
    name="3b-bot",
    version=__version__,
    description="A bot for quickly purchasing items from Best Buy when they come back in stock.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Leon Shams-Schaal",
    url="https://github.com/LeonShams/BestBuyBulletBot",
    project_urls={
        "Documentation": "https://github.com/LeonShams/BestBuyBulletBot/wiki",
        "Bug Tracker": "https://github.com/LeonShams/BestBuyBulletBot/issues",
    },
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=Path("requirements.txt").read_text().splitlines(),
    entry_points={"console_scripts": ["3b-bot=best_buy_bullet_bot.command_line:main"]},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    license="MIT",
    keywords="bestbuy bot bestbuybot bestbuybulletbot 3bbot 3b-bot restock \
        bestbuystock bestbuytracker stocktracker bestbuystocktracker \
        autocheckout bestbuyautocheckout",
)
