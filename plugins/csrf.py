#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(255, 0, 255)


def check(data: Data.Data, lock: Lock):
    csrf_results = Data.CheckResults("CSRF", COLOR)
    csrf_results.page_results.append(Data.PageResult(data.pages[0], "random problem", "random solution"))
    lock.acquire()
    data.results.append(csrf_results)
    lock.release()
