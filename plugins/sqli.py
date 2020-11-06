#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data

COLOR = COLOR_MANAGER.rgb(255, 100, 0)


def check(data: Data.Data):
    print(COLOR + COLOR_MANAGER.BOLD + "- SQL Injection check:" + COLOR_MANAGER.ENDC)
    print(COLOR + "\tnope, nothing yet")
