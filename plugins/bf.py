#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(0, 255, 0)


def check(data: Data.Data, lock: Lock):
    lock.acquire()
    print(COLOR + COLOR_MANAGER.BOLD + "- Brute Force check:" + COLOR_MANAGER.ENDC)
    print(COLOR + "\tnope, nothing yet")
    lock.release()
