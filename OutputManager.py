#!/usr/bin/python3
import Classes
from colors import *
import threading
import xml.etree.ElementTree as ET


def print_results(check_results):
    """
    This function prints the latest check results.
    @type check_results: Classes.CheckResults
    @param check_results: The check results given by the plugins.
    @return: None
    """
    color = check_results.color
    print(f"{COLOR_MANAGER.BOLD}{color}- {COLOR_MANAGER.UNDERLINE}"
          f"{check_results.headline}:{COLOR_MANAGER.ENDC}")
    if check_results.error:
        COLOR_MANAGER.print_error(check_results.error, "\t")
        return
    if check_results.warning:
        COLOR_MANAGER.print_warning(check_results.warning, "\t")
        return
    if check_results.success:
        COLOR_MANAGER.print_success(check_results.success, "\t")
    if all(not check_result.page_results for check_result in check_results.results):
        COLOR_MANAGER.print_success("No vulnerabilities were found on the specified website's pages.\n", "\t")
        return
    for check_result in check_results.results:
        print_check_result(check_result, color)
    if check_results.conclusion:
        print(f"\t{COLOR_MANAGER.BOLD_PURPLE}Conclusion:"
              f" {COLOR_MANAGER.ENDC}{color}{check_results.conclusion}")


def print_check_result(check_result, color):
    """
    Function prints a specific check result
    @type check_result: Classes.CheckResult
    @param check_result: The printed check result
    @type color: str
    @param color: The color of the text
    @return: None
    """
    def print_lines(message, first_line_start, new_line_start):
        """
        Inner function separates the lines of the message
        @type message: str
        @param message: The message to print
        @type first_line_start: str
        @param first_line_start: First line begins with this string
        @type new_line_start: str
        @param new_line_start: Every new line begins with this string
        @return: None
        """
        index = 0
        for line in message.split("\n"):
            if not index:
                # First line.
                print(f"{first_line_start}{color}{line}")
            else:
                # Any other line
                print(f"{new_line_start}{color}{line}")
            index += 1
    if not check_result.page_results:
        return
    for page_result in check_result.page_results:
        print(f"\t{COLOR_MANAGER.ENDC}[{color}*{COLOR_MANAGER.ENDC}]"
              f" {color}{page_result.url}")
        if page_result.description:
            print_lines(page_result.description, "\t\t- ", "\t\t- ")
    if check_result.problem:
        print_lines(check_result.problem,
                    f"\t{COLOR_MANAGER.BOLD_RED}Problem: {COLOR_MANAGER.ENDC}",
                    "\t" + len("Problem: ") * " ")
    if check_result.solution:
        print_lines(check_result.solution,
                    f"\t{COLOR_MANAGER.BOLD_GREEN}Solution: {COLOR_MANAGER.ENDC}",
                    "\t" + len("Solution: ") * " ")
    print("")


def save_results(data):
    """
    This function saves the results to the xml output file.
    @type data: Classes.Data
    @param data: The data object of the program.
    @return None
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


def logic(data, all_threads_done_event):
    """
    This function controls the general output of the plugins to the screen,
    prints the check results to the screen or to a xml file and prints the print queue.
    @type data: Classes.Data
    @param data: The data object of the program.
    @type all_threads_done_event: threading.Event
    @param all_threads_done_event: Signals when all the plugins have finished their run.
    @return None
    """
    def empty_the_queue():
        # Check if there is anything to print.
        data.mutex.acquire()
        while not data.results_queue.empty():
            # Print the print queue.
            print_results(data.results_queue.get())
        data.mutex.release()

    print(f"\t{COLOR_MANAGER.PURPLE}Waiting for the plugins to finish their run...{COLOR_MANAGER.ENDC}")
    if data.output is None:
        # There is no need to save results to an output file.
        while not all_threads_done_event.isSet():
            # While the plugins are still running.
            empty_the_queue()
        empty_the_queue()
    else:
        # If there is a specified output file path.
        all_threads_done_event.wait()  # Waiting for the plugins to finish their run.
        print(f"\t{COLOR_MANAGER.BOLD}{COLOR_MANAGER.GREEN}Saving Results to Output File"
              f" ({data.output})...{COLOR_MANAGER.ENDC}")
        save_results(data)  # Saving the results in the output file.
