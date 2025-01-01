from setuptools import setup, find_packages

from mangadm import __version__


def parse_requirements(filename):
    with open(filename, "r", encoding="utf8") as f:
        requirements = f.read().strip().split("\n")
        requirements = [
            r.strip() for r in requirements if r.strip() and not r.startswith("#")
        ]
        return requirements


setup(
    name="MangaDM",
    version=__version__,
    description="A command-line tool and Python library for downloading manga chapters based on the metadata specified in a JSON file.",
    packages=find_packages(),
    include_package_data=True,
    install_requires=parse_requirements("requirements.txt"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "mangadm=mangadm.core.cli:cli",
        ],
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/xMohnad/MangaDM",
)
