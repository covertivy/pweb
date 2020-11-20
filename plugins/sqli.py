#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 100, 0)


def check(data: Data.Data, lock: Lock):
    sqli_results = Data.CheckResults("SQL Injection", COLOR)
    sqli_results.page_results.append(Data.PageResult(Data.Page("", "", ""), "random problem", "random solution"))
    lock.acquire()
    data.results.append(sqli_results)
    lock.release()
