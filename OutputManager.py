#!/usr/bin/python3
import Data
from colors import *
import threading
import xml.etree.ElementTree as ET


def print_results(results: Data.CheckResults) -> None:
    print(
        f"{COLOR_MANAGER.BOLD}{results.color}- {COLOR_MANAGER.UNDERLINE}{results.headline}:{COLOR_MANAGER.ENDC}{results.color}"
    )
    for res in results.page_results:
        if res.problem is not None and res.solution is not None:
            print(
                f"\t{COLOR_MANAGER.BOLD}Page: {COLOR_MANAGER.ENDC}{results.color}{res.url}\n"
                f"\t\t{COLOR_MANAGER.BOLD}Problem: {COLOR_MANAGER.ENDC}{results.color}{res.problem}\n"
                f"\t\t{COLOR_MANAGER.BOLD}Solution: {COLOR_MANAGER.ENDC}{results.color}{res.solution}"
            )


def save_results(data) -> None:
    """
    A function that saves the results to the xml output file.
    """
    root = ET.Element("root", name="root")  # Create a root for the element tree.
    for thread_results in data.results:
        # Go over each script's findings and summarize them.
        script_element = ET.SubElement(root, thread_results.headline.replace(" ", "_"))
        for page_res in thread_results.page_results:
            # Save each page's data in an xml tree format.
            page_element = ET.SubElement(script_element, "Page")
            page_url_element = ET.SubElement(page_element, "url")
            page_url_element.text = str(page_res.url)
            page_status_element = ET.SubElement(page_element, "status")
            page_status_element.text = str(page_res.status)
            page_result_problem_element = ET.SubElement(page_element, "problem")
            page_result_problem_element.text = str(page_res.problem)
            page_result_solution_element = ET.SubElement(page_element, "solution")
            page_result_solution_element.text = str(page_res.solution)
    # Create the tree with the `root` element as the root.
    tree = ET.ElementTree(root)
    with open(data.output, "w") as f:
        tree.write(f, encoding="unicode")


def logic(data: Data.Data, mutex: threading.Lock, all_threads_done_event: threading.Event) -> None:
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
        print(
            f"\t{COLOR_MANAGER.PURPLE}Waiting for the plugins to finish their run...{COLOR_MANAGER.ENDC}"
        )
        all_threads_done_event.wait()  # Waiting for the plugins to finish their run
        print(
            f"\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving to Output File ({data.output})...{COLOR_MANAGER.ENDC}"
        )
        save_results(data)  # Saving the results
