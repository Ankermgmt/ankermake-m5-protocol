"""
This module imports the 'Path' class from the 'pathlib' package and sets the ROOT_DIR variable. 'Path' from 'pathlib'
provides a more object-oriented method to handle filesystem paths.

Variables:
- ROOT_DIR: A Path object pointing to the parent directory of the file this code is in.

Usage:
- Import this module into your script, then access the ROOT_DIR variable to get the parent directory Path object
for your project.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
