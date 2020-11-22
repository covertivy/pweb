#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 0, 100)


def check(data: Data.Data, lock: Lock):
    xss_results = Data.CheckResults("XSS", COLOR)
    xss_results.page_results.append(Data.PageResult(Data.Page("", "", ""), "random problem", "random solution"))
    lock.acquire()
    data.results.append(xss_results)
    lock.release()
