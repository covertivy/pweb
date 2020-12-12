#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from threading import Lock

COLOR = COLOR_MANAGER.rgb(0, 200, 200)


def check(data: Data.Data):
    fi_results = Data.CheckResults("File Inclusion", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()
    for page in pages:
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        fi_results.page_results.append(res)
    data.mutex.acquire()
    data.results.append(fi_results)
    data.mutex.release()
