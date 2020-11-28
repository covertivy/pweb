#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 255, 0)


def check(data: Data.Data, lock: Lock):
    ci_results = Data.CheckResults("Command Injection", COLOR)
    lock.acquire()
    pages = data.pages
    lock.release()
    for page in pages:
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        ci_results.page_results.append(res)
    lock.acquire()
    data.results.append(ci_results)
    lock.release()
