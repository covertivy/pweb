#!/usr/bin/python3
import Data
from colors import *
import os
from os import path
import threading
import xml.etree.ElementTree as ET


def print_results(res_dict: Data.CheckResults) -> None:
    print(f"{COLOR_MANAGER.BOLD}{res_dict.color}- {COLOR_MANAGER.UNDERLINE}{res_dict.headline}:{COLOR_MANAGER.ENDC}{res_dict.color}")
    [
        print(f"\t{COLOR_MANAGER.BOLD}Page: {COLOR_MANAGER.ENDC}{res_dict.color}{r.url}\n"
              f"\t\t{COLOR_MANAGER.BOLD}Problem: {COLOR_MANAGER.ENDC}{res_dict.color}{r.problem}\n"
              f"\t\t{COLOR_MANAGER.BOLD}Solution: {COLOR_MANAGER.ENDC}{res_dict.color}{r.solution}")
        for r in res_dict.page_results
    ]


def save_results(data: Data.Data) -> None:
    """
    A function that saves the results to the output file.
    Args:
        res_dict (dict): The dictionary of each script and it's results.
        path (str): The output file's path.
    """
    root = ET.Element("root")
    for thread_results in data.results:
        script_element = ET.SubElement(root, thread_results.headline)
        for page_res in thread_results.page_results:
            page_result_element = ET.SubElement(script_element, page_res.url)
            page_status = ET.SubElement(page_result_element, page_res.status)
            page_result_problem = ET.SubElement(page_result_element, page_res.problem)
            page_result_solution = ET.SubElement(page_result_element, page_res.solution)
    tree = ET.ElementTree(root)
    with open(data.output, "w") as f:
        tree.write(f, encoding="unicode")


def logic(
    data: Data.Data,
    mutex: threading.Lock,
    all_threads_done_event: threading.Event) -> None:
    index = 0
    if data.output is None:
        # If there is no specified file path
        while True:
            # While the plugins are still running
            if len(data.results) == index:
                #  If there are no new results
                if all_threads_done_event.isSet():
                    #  If all the threads has finished their run
                    break
                else:
                    continue
            else:
                # If there are new results
                mutex.acquire()
                results = data.results[index]  # The most recent results.
                mutex.release()
                index += 1
                # Print the current found results.
                print_results(results)
    else:
        # If there is a specified file path
        print("Waiting for the plugins to finish their run...")
        all_threads_done_event.wait()  # Waiting for the plugins to finish their run
        print(
            f"{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving to Output File ({data.output})...{COLOR_MANAGER.ENDC}"
        )
        save_results(data)  # Saving the results
