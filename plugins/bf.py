#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(0, 255, 0)


def check(data: Data.Data, lock: Lock):
    results = Data.CheckResults("Brute Force", COLOR)
    results.results.append(Data.PageResult(Data.Page("", "", ""), "random problem", "random solution"))
    lock.acquire()
    data.results.append(results)
    lock.release()
