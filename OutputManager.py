#!/usr/bin/python3
from Data import Data, CheckResults
from colors import *
import threading
import xml.etree.ElementTree as ET


def print_results(results: CheckResults):
    """
    Function prints the latest check results
    @param results: The check results
    @return:
    """
    if results.page_results:
        print(f"{COLOR_MANAGER.BOLD}{results.color}- {COLOR_MANAGER.UNDERLINE}{results.headline}:"
              f"{COLOR_MANAGER.ENDC}{results.color}")
        for res in results.page_results:
            print(f"\t{COLOR_MANAGER.BOLD}Page: {COLOR_MANAGER.ENDC}{results.color}{res.url}")
            if res.problem:
                print(f"\t\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.RED}Problem: {COLOR_MANAGER.ENDC}{results.color}{res.problem}")
            if res.solution:
                print(f"\t\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Solution: {COLOR_MANAGER.ENDC}{results.color}{res.solution}")
        return True
    return False


def save_results(data):
    """
    Function saves the results to the xml output file
    @param data: The data object of the program
    @return: None
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


def logic(data: Data, all_threads_done_event: threading.Event):
    """
    Function prints the check results to the screen or to a xml file
    @param data: The data object of the program
    @param all_threads_done_event: Signals when the plugins has finished their run
    @return: None
    """
    index = 0
    if data.output is None:
        # If there is no specified file path
        found_vulnerability = False
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
                data.mutex.acquire()
                results = data.results[index]  # The most recent results.
                data.mutex.release()
                index += 1
                # Print the current found results.
                if print_results(results):
                    found_vulnerability = True
        if not found_vulnerability:
            print(f"\t{COLOR_MANAGER.PURPLE}Did not find any vulnerability...{COLOR_MANAGER.ENDC}")
    else:
        # If there is a specified file path
        print(
            f"\t{COLOR_MANAGER.PURPLE}Waiting for the plugins to finish their run...{COLOR_MANAGER.ENDC}")
        all_threads_done_event.wait()  # Waiting for the plugins to finish their run
        print(
            f"\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving to Output File ({data.output})...{COLOR_MANAGER.ENDC}")
        save_results(data)  # Saving the results
