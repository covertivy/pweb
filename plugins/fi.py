#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(0, 200, 200)


def check(data: Data.Data, lock: Lock):
    fi_results = Data.CheckResults("File Inclusion", COLOR)
    lock.acquire()
    pages = data.pages
    lock.release()
    for page in pages:
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        fi_results.page_results.append(res)
    lock.acquire()
    data.results.append(fi_results)
    lock.release()
