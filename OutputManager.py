#!/usr/bin/python3
import Data
from colors import *
import os
from os import path
import threading
import xml.etree.ElementTree as ET


def print_results(res_dict: Data.CheckResults) -> None:
    print(f"{res_dict.color}- {res_dict.headline}:")
    [
        print(f"\tProblem: {r.problem}\n\tSolution: {r.solution}")
        for r in res_dict.page_results
    ]


def save_results(res_list, path: str) -> None:
    """
    A function that saves the results to the output file.
    Args:
        res_dict (dict): The dictionary of each script and it's results.
        path (str): The output file's path.
    """
    root = ET.Element("root", name="root")
    for thread_results in res_list:
        script_element = ET.SubElement(root, thread_results.headline.replace(" ", "_"))
        for page_res in thread_results.page_results:
            page_element = ET.SubElement(script_element, "Page")
            page_url_element = ET.SubElement(page_element, "url")
            page_url_element.text = page_res.url
            page_status_element = ET.SubElement(page_element, "status")
            page_status_element.text = page_res.status
            page_result_problem_element = ET.SubElement(page_element, "problem")
            page_result_problem_element.text = page_res.problem
            page_result_solution_element = ET.SubElement(page_element, "solution")
            page_result_solution_element.text = page_res.solution
    tree = ET.ElementTree(root)
    with open(path, "w") as f:
        tree.write(f, encoding="unicode")


def logic(
    data: Data.Data,
    mutex: threading.Lock,
    info: list,
    all_threads_done_event: threading.Event,
) -> None:
    index = 0
    if data.output is None:  # Check if output file was given.
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
                results = data.results[index]  # The recent results.
                mutex.release()
                index += 1
                # Print the current found results.
                print_results(results)
    else:
        all_threads_done_event.wait()
        mutex.acquire()
        all_results = data.results  # All the results.
        mutex.release()

        print(
            f"{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving to Output File ({data.output})...{COLOR_MANAGER.ENDC}"
        )
        save_results(all_results, data.output)
