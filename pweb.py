#!/usr/bin/python3
from Classes import Data
import FlagManager
import PluginManager
import AddressManager
import PageManager
import VulnerabilityManager
from colors import COLOR_MANAGER
import os
import psutil


def print_data(data: Data):
    """
    This function prints the given data object to the console in a nice format.

    @param data: The data object of the program.
    @type data: Data
    @return: None
    """
    print(f"\n{COLOR_MANAGER.PINK + COLOR_MANAGER.HEADER}Inserted data:{COLOR_MANAGER.ENDC}")
    for line in str(data).split("\n"):
        print(f"\t[{COLOR_MANAGER.PINK}*{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.PINK}{line}{COLOR_MANAGER.ENDC}")
    print(COLOR_MANAGER.ENDC)


def main():
    """
    This function connects the different managers together.
    
    @return: None
    """
    try:
        # Initiate manager classes instances.
        data = Data()
        function_order = [
            FlagManager.FlagManager().logic,  # Get arguments from command line.
            AddressManager.AddressManager().logic,  # Check specified address.
            print_data,  # Print given arguments.
            PageManager.PageManager().logic,  # Get all the pages from the website.
            PluginManager.PluginManager().logic,  # Generate the `Check Device` in our directory.
            VulnerabilityManager.VulnerabilityManager().logic  # Run plugins with the `Check Device`.
        ]
        # Starting the process.
        for function in function_order:
            # Executing every function.
            function(data)
        print(COLOR_MANAGER.ENDC)
    except KeyboardInterrupt:
        # The user pressed ctrl+c.
        COLOR_MANAGER.print_warning("You have decided to close the process, please wait few seconds...\n", "\n\t")
    except Exception as e:
        if len(e.args) == 2:
            COLOR_MANAGER.print_error(str(e.args[0]), str(e.args[1]))
        else:
            COLOR_MANAGER.print_error(str(e))
    finally:
        # Every time the program has finished it's run we clean up.
        finishing_up()


def finishing_up():
    """
    Every time the program has finished we need to remove every instance of ChromeDriver processes from memory.

    @return: None
    """
    try:
        # We check if we have deleted every chromedriver instance.
        for proc in psutil.process_iter():
            try:
                if "chrome" in proc.name() and '--test-type=webdriver' in proc.cmdline():
                    psutil.Process(proc.pid).terminate()  # Deleting chromedriver processes from memory.
            except Exception:
                # In case of required permission.
                continue
        # Deleting the `check device` file after the program has finished it's run.
        if os.path.exists('CheckDevice.py'):
            os.remove('CheckDevice.py')
        exit()
    except KeyboardInterrupt:
        # If we are interrupted we must check again to prevent partial deletion of processes.
        finishing_up()


if __name__ == "__main__":
    main()
