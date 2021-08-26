from pathlib import Path

from setuptools import find_packages, setup

# Get __version__ from best_buy_bullet_bot/version.py
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
    author="Leon Shams-Schaal",
    description="Quickly purchase items from Best Buy the moment they restock.",
    long_description=Path("readme.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/LeonShams/BestBuyBulletBot",
    project_urls={
        "Documentation": "https://github.com/LeonShams/BestBuyBulletBot/wiki",
        "Bug Tracker": "https://github.com/LeonShams/BestBuyBulletBot/issues",
    },
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=Path("requirements.txt").read_text().splitlines(),
    entry_points={"console_scripts": ["3b-bot=best_buy_bullet_bot.__main__:main"]},
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Environment :: Console",
    ],
    keywords="bestbuy bot bestbuybot bestbuybulletbot 3bbot 3b-bot bestbuystock \
        bestbuyrestock bestbuytracker stocktracker bestbuystocktracker \
        autocheckout bestbuyautocheckout nvidiabot gpubot nvidiagpubot \
        3060bot 3060tibot 3070bot 3070tibot 3080bot 3080tibot 3090bot \
        ps5bot nvidiatracker gputracker nvidiagputracker 3060tracker \
        3060titracker 3070tracker 3070titracker 3080tracker 3080titracker \
        3090tracker ps5tracker",
)
