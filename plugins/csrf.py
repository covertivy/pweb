#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 0, 255)


def check(data: Data.Data, lock: Lock):
    csrf_results = Data.CheckResults("CSRF", COLOR)
    lock.acquire()
    pages = data.pages
    lock.release()
    for page in pages:
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        csrf_results.page_results.append(res)
    lock.acquire()
    data.results.append(csrf_results)
    lock.release()
