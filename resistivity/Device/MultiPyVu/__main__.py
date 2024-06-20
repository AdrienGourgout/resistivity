#!/usr/bin/env python3
"""
This allows people to start the MultiPyVu Server gui using the -m flag and the module name.

> python -m MultiPyVu

One can run this in scaffolding mode by adding adding flags
when calling this script.

For example:
> python -m MultiPyVu -s opticool

@author: djackson
"""

import sys

from MultiPyVu.Controller import Controller as gui


def main():
    server = gui(sys.argv[1:])
    server.start_gui()


if __name__ == '__main__':
    main()
