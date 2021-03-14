#!/usr/bin/python3
import Classes
from colors import *
import threading
import xml.etree.ElementTree as ET


def print_results(results: Classes.CheckResults):
    """
    This function prints the latest check results.
    @param results: The check results given by the plugins.
    @return: None
    """
    print(f"{COLOR_MANAGER.BOLD}{results.color}- {COLOR_MANAGER.UNDERLINE}{results.headline}:"
          f"{COLOR_MANAGER.ENDC}{results.color}")
    if type(results.page_results) == list:
        if not len(results.page_results):
            COLOR_MANAGER.print_success("No vulnerabilities were found on the specified website's pages.", "\t")
        for res in results.page_results:
            print(f"\t{COLOR_MANAGER.BOLD}Page: {COLOR_MANAGER.ENDC}{results.color}{res.url}")
            if res.problem:
                print(f"\t\t{COLOR_MANAGER.BOLD_RED}Problem:"
                      f" {COLOR_MANAGER.ENDC}{results.color}{res.problem}")
            if res.solution:
                print(f"\t\t{COLOR_MANAGER.BOLD_GREEN}Solution:"
                      f" {COLOR_MANAGER.ENDC}{results.color}{res.solution}")
            print("")
    elif type(results.page_results) == str:
        COLOR_MANAGER.print_error(results.page_results, "\t")
    else:
        COLOR_MANAGER.print_error("Something went wrong", "\t")


def save_results(data: Classes.Data):
    """
    This function saves the results to the xml output file.
    @param data (Classes.Data): The data object of the program.
    @returns None.
    """
    root = ET.Element("root", name="root")  # Create a root for the element tree.
    for thread_results in data.results:
        # Go over each script's findings and summarize them.
        if len(thread_results.page_results) == 0:
            continue
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


def logic(data: Classes.Data, all_threads_done_event: threading.Event):
    """
    This function controls the general output of the plugins to the screen,
    prints the check results to the screen or to a xml file and prints the print queue.
    @param data (Classes.Data): The data object of the program.
    @param all_threads_done_event (threading.Event): Signals when all the plugins have finished their run.
    @returns None.
    """
    index = 0
    print(f"\t{COLOR_MANAGER.PURPLE}Waiting for the plugins to finish their run...{COLOR_MANAGER.ENDC}")
    if data.output is None:
        # There is no need to save results to an output file.
        while True:
            # While the plugins are still running.
            data.mutex.acquire()
            if len(data.results) == index:
                # If there are no new results.
                if all_threads_done_event.isSet():
                    # If all the threads has finished their run.
                    data.mutex.release()
                    break
                else:
                    data.mutex.release()
                    continue
            else:
                # If there are new results.
                results = data.results[index]  # The most recent results.
                data.mutex.release()
                index += 1
                # Print the current found results.
                print_results(results)
            
            data.mutex.acquire()
            # Check if there is anything to print.
            while data.print_queue.not_empty:
                # Print the print queue.
                curr: tuple = data.print_queue.get()
                # Validate print request.
                if curr is not None and len(curr) == 2:
                    print(f"{curr[0]}: {curr[1]}")
                # If request is not valid simply continue to the next one.
            data.mutex.release()
    else:
        # If there is a specified output file path.
        all_threads_done_event.wait()  # Waiting for the plugins to finish their run.
        print(f"\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving Results to Output File"
              f" ({data.output})...{COLOR_MANAGER.ENDC}")
        save_results(data)  # Saving the results in the output file.
