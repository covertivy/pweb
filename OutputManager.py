#!/usr/bin/python3
import Classes
from colors import *
import os


class OutputManager(Classes.Manager):
    def __init__(self):
        self.__folder = str()
        self.__files = dict()

    @staticmethod
    def __manage_lines(message, color, first_line_start, new_line_start):
        """
        Function separates the lines of the message
        @type message: str
        @param message: The message to print
        @type color: str
        @param color: The color of the printed message.
        @type first_line_start: str
        @param first_line_start: First line begins with this string
        @type new_line_start: str
        @param new_line_start: Every new line begins with this string
        @rtype: str
        @return: A line output string
        """
        index = 0
        output = str()
        for line in message.split("\n"):
            if not index:
                # First line.
                output += f"{first_line_start}{color}{line}\n"
            else:
                # Any other line
                output += f"{new_line_start}{color}{line}\n"
            index += 1
        return output

    def __manage_check_result(self, check_result, color):
        """
        Function prints a specific check result
        @type check_result: Classes.CheckResult
        @param check_result: The printed check result
        @type color: str
        @param color: The color of the text
        @rtype: str
        @return: The check result output string
        """
        output = str()
        if not check_result.page_results:
            return output
        for page_result in check_result.page_results:
            output += f"\t{COLOR_MANAGER.ENDC}[{color}*{COLOR_MANAGER.ENDC}] {color}{page_result.url}\n"
            if page_result.description:
                output += self.__manage_lines(page_result.description, color, "\t\t- ", "\t\t  ")
        if check_result.problem:
            output += self.__manage_lines(check_result.problem, color,
                                          f"\t{COLOR_MANAGER.BOLD_RED}Problem: {COLOR_MANAGER.ENDC}",
                                          "\t" + len("Problem: ") * " ")
        if check_result.solution:
            output += self.__manage_lines(check_result.solution, color,
                                          f"\t{COLOR_MANAGER.BOLD_GREEN}Solution: {COLOR_MANAGER.ENDC}",
                                          "\t" + len("Solution: ") * " ")
        if check_result.explanation:
            output += self.__manage_lines(check_result.explanation, color,
                                          f"\t{COLOR_MANAGER.BOLD_LIGHT_GREEN}Explanation: {COLOR_MANAGER.ENDC}",
                                          "\t" + len("Explanation: ") * " ")
        return output

    def __manage_check_results(self, check_results, color):
        """
        This function prints the latest check results.
        @type check_results: Classes.CheckResults
        @param check_results: The check results given by the plugins.
        @rtype: str
        @return: The check results output string
        """
        output = f"{COLOR_MANAGER.BOLD}{color}- {COLOR_MANAGER.UNDERLINE}" \
                 f"{check_results.headline}:{COLOR_MANAGER.ENDC}\n"
        if check_results.warning:
            output += COLOR_MANAGER.warning_message(check_results.warning, "\t", "\n\n")
        if check_results.error:
            output += COLOR_MANAGER.error_message(check_results.error, "\t", "\n\n")
        if all(not check_result.page_results for check_result in check_results.results):
            if check_results.success:
                output += COLOR_MANAGER.success_message(check_results.success, "\t", "\n\n")
            if not check_results.error and not check_results.warning:
                output += COLOR_MANAGER.success_message("No vulnerabilities were "
                                                        "found on the specified website's pages.",
                                                        "\t", "\n")
            return output
        for check_result in check_results.results:
            output += self.__manage_check_result(check_result, color)
        if check_results.conclusion:
            output += self.__manage_lines(check_results.conclusion, color,
                                          f"\t{COLOR_MANAGER.BOLD_PURPLE}Conclusion: {COLOR_MANAGER.ENDC}",
                                          "\t" + len("Conclusion: ") * " ")
        return output

    def __save_results(self):
        """
        This function saves the results to the xml output file.
        @return None
        """
        if not self.__files:
            COLOR_MANAGER.print_error("Looks like there is nothing to save to the files, try again.", "\n\t", "\n")
            return
        COLOR_MANAGER.print_success(f"Saving Results to Output Files in {self.__folder} folder...", "\n\t", "\n")
        for file in self.__files.keys():
            path = os.path.join(self.__folder, file + ".txt")
            with open(path, "w") as f:
                f.write(self.__files[file])

    def __manage_output(self, check_results):
        """
        Function take the current check results, generate its output and print or save it to a file.
        @type check_results: Classes.CheckResults
        @param check_results: The check results given by the plugins.
        @return: None
        """
        color = "" if self.__folder else check_results.color
        output = self.__manage_check_results(check_results, color)
        if not self.__folder:
            # Printing the message to the screen
            print(output)
        else:
            # Adding the file name and it's content to the dictionary
            self.__files[check_results.headline] = COLOR_MANAGER.remove_colors(output)

    def logic(self, data):
        """
        This function controls the general output of the plugins to the screen,
        prints the check results to the screen or to a xml file and prints the print queue.
        @type data: Classes.Data
        @param data: The data object of the program.
        @return None
        """
        if data.output:
            # The user specified a directory path.
            if os.path.exists(data.output):
                # Folder already exists.
                COLOR_MANAGER.print_warning("Saving output to an already existing folder.", "\t", "\n")
                self.__folder = os.path.abspath(data.output)
            else:
                # Folder does not exist.
                try:
                    os.mkdir(data.output)
                    self.__folder = os.path.abspath(data.output)
                    COLOR_MANAGER.print_success("Successfully created the output folder.", "\t", "\n")
                except OSError as e:
                    COLOR_MANAGER.print_error("Invalid folder path, printing the output instead.", "\t", "\n")

        print(f"\t{COLOR_MANAGER.PURPLE}Waiting for the plugins to finish their run...{COLOR_MANAGER.ENDC}")

        def empty_the_queue():
            # Check if there is anything to print.
            data.mutex.acquire()
            while not data.results_queue.empty():
                # Print the print queue.
                self.__manage_output(data.results_queue.get())
            data.mutex.release()

        while not data.all_threads_done_event.isSet():
            # While the plugins are still running.
            empty_the_queue()
        empty_the_queue()

        if self.__folder:
            self.__save_results()  # Saving the results in the output file.
