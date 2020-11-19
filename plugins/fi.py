#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(0, 200, 200)


def check(data: Data.Data, lock: Lock):
    results = Data.CheckResults("File Inclusion", COLOR)
    results.results.append(Data.PageResult(Data.Page("", "", ""), "random problem", "random solution"))
    lock.acquire()
    data.results.append(results)
    lock.release()
