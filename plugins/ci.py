#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 255, 0)


def check(data: Data.Data, lock: Lock):
    ci_results = Data.CheckResults("Command Injection", COLOR)
    ci_results.page_results.append(Data.PageResult(Data.Page("", "", ""), "random problem", "random solution"))
    lock.acquire()
    data.results.append(ci_results)
    lock.release()
