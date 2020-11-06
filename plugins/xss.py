#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data

COLOR = COLOR_MANAGER.rgb(255, 0, 100)


def check(data: Data.Data):
    print(COLOR + COLOR_MANAGER.BOLD + "- XSS check:" + COLOR_MANAGER.ENDC)
    print(COLOR + "\tnope, nothing yet")
