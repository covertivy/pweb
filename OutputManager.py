#!/usr/bin/python3
import Data
import os
from os import path
import threading


def print_results(res_dict: Data.CheckResults) -> None:
    print(f"{res_dict.color}- {res_dict.headline}:")
    [
        print(f"\tProblem: {r.problem}\n\tSolution: {r.solution}")
        for r in res_dict.page_results
    ]


def print_results(res_dict: dict) -> None:
    for script in res_dict.keys():
        pass


def save_results(res_dict: Data.CheckResults, path: str, clean_save: bool) -> None:
    """
    A function that saves the results to the output folder.
    Args:
        res_dict (dict): The dictionary of each script and it's results.
        path (str): The output folder's path.
        clean_save (bool): A flag to indicate if the save is occuring on a clean folder (True) or an existing one (False).
    """
    for result in res_dict.keys():
        pass


def logic(data: Data.Data, mutex: threading.Lock, info: list) -> None:
    index = 0
    while index < info[0]:
        # While the number of results that were handled are less the number of plugins
        if len(data.results) == index:
            #  There are no new results
            if info[1]:
                #  info[1] is a bool, False = there are threads that are still running
                #  True = all the threads have finished their run
                break
            else:
                continue
        else:
            mutex.acquire()
            results = data.results[index]  # The recent results
            mutex.release()
            index += 1
            if data.folder is None:  # Check if output folder was given.
                print_results(results)
            elif not path.exists(data.folder):  # Check if given output folder exists
                print(f"Creating Output Folder ({data.folder})...")
                os.makedirs(data.folder)  # Create non existent dir tree.
                save_results(results, data.folder, True)
            else:  # Output folder exists.
                print(f"Saving to existing Output Folder ({data.folder})...")
                save_results(results, data.folder, False)
