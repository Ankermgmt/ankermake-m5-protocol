""" This module imports the 'path' module from the 'os' package and sets the ROOT_DIR variable.

Imports: - os.path: Provides functions to interact with file paths.

Variables: - ROOT_DIR: A string containing the absolute path of the parent directory of the file this code is in.

Usage: - Import this module into your script, then access the ROOT_DIR variable \
to get the absolute path of the parent directory for your project. """
from os import path

ROOT_DIR = path.realpath(path.join(path.dirname(__file__), '..'))
