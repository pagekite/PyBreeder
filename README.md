## THIS IS OBSOLETE

This tool is no longer maintained and is considered obsolete.

Please consider using [zipapp](https://docs.python.org/3/library/zipapp.html) instead, as it should be both more elegant and more performant.

# Breeder #

This is a quick-and-dirty tool for combining multiple .py (or other text)
files into a single script, making it easier to distribute/deploy Python
scripts along with their dependencies.

Usage example:

    breeder.py module1.py directory/ ... main.py >big-snake.py

All Python files (and directories) will be treated as modules, except the last
one which will be treated as the 'main' body of the combined script.  It is up
to the caller to figure out which order to import files in, if there is are
dependencies between modules.

To compress modules and embedded data, add the `--compress` flag.

To include a custom header at the top of the file, use `--header FILENAME`.

Breeder output scripts have been verified to be compatible as far back as
Python 2.2.2 and should work with any Python 2.x release.

**Note:** If you know you are targetting Python 2.6 or newer, you should
probably use Python's native .zip support instead of this hack!


## Copyright ##

Breeder is (C) Copyright 2011, Bjarni R. Einarsson <http://bre.klaki.net/>.

TODO: GPLv3

