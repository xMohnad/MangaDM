import shutil
import os
from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstallCommand(install):
    def run(self):
        # Call the standard install process
        install.run(self)
        
        # Now perform post-installation tasks
        self.copy_completion_file()

    def copy_completion_file(self):
        home = os.path.expanduser("~")
        fish_completion_dir = os.path.join(home, ".config", "fish", "completions")
        
        # Create the completions directory if it doesn't exist
        if not os.path.exists(fish_completion_dir):
            os.makedirs(fish_completion_dir)
        
        # Source and destination file paths
        source_file = os.path.join(os.path.dirname(__file__), 'completion', 'MangaDM.fish')
        dest_file = os.path.join(fish_completion_dir, 'MangaDM.fish')
        
        # Copy the file if it exists
        if os.path.isfile(source_file):
            shutil.copy(source_file, dest_file)
            print(f"Copied {source_file} to {dest_file}")
        else:
            print(f"Error: {source_file} does not exist.")

setup(
    name="MangaDM",
    version="0.5",
    packages=find_packages(),
    install_requires=[
        "click", "requests", 
        "rich", "InquirerPy", 
        "click-completion"
        ],
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
    cmdclass={
        'install': CustomInstallCommand,
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/xMohnad/MangaDM",
)
