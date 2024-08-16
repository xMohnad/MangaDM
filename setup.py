from setuptools import setup, find_packages

setup(
    name="MangaDM",
    version="0.2",
    packages=find_packages(),
    install_requires=["click", "requests", "rich"],
    entry_points={
        "console_scripts": [
            "manga-dm=manga_dm.cli:cli",
        ],
    },
)