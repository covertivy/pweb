#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 255, 0)


def check(data: Data.Data):
    ci_results = Data.CheckResults("Command Injection", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()
    for page in pages:
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        ci_results.page_results.append(res)
    data.mutex.acquire()
    data.results.append(ci_results)
    data.mutex.release()
