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
    Function prints the inserted data
    @param data: The data object of the program
    @return: None
    """
    print(f"\n{COLOR_MANAGER.PINK + COLOR_MANAGER.HEADER}Inserted data:{COLOR_MANAGER.ENDC}")
    for line in str(data).split("\n"):
        print(f"\t[{COLOR_MANAGER.PINK}*{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.PINK}{line}{COLOR_MANAGER.ENDC}")
    print(COLOR_MANAGER.ENDC)


def main():
    """
    Function connects the different managers together
    @return: None
    """
    os.system("color")  # Without it, the COLOR_MANAGER won't work.
    try:
        data = FlagManager.get_final_args(FlagManager.parse_args())  # Get arguments from command line.
        # AddressManager.set_target(data)  # Check specified address
        print_data(data)  # Print specified arguments
        PageManager.logic(data)  # Get all pages from website.
        PluginManager.generate_check_device()  # Generate Check Device in our directory.
        VulnerabilityManager.logic(data)
        print(COLOR_MANAGER.ENDC)
    except KeyboardInterrupt as e:
        # The user pressed ctrl+c
        COLOR_MANAGER.print_warning("You have decided to close the process, please wait few seconds...\n", "\n\t")
    except Exception as e:
        if len(e.args) == 2:
            COLOR_MANAGER.print_error(str(e.args[0]), str(e.args[1]))
        else:
            COLOR_MANAGER.print_error(str(e))
    finally:
        # Every time the program has finished it's run.
        finishing_up()


def finishing_up():
    """
    Every time the program has finished, we need to remove every Chromedriver
    @return: None
    """
    try:
        # We make sure it deleted every chromedriver.
        for proc in psutil.process_iter():
            try:
                if "chrome" in proc.name() and '--test-type=webdriver' in proc.cmdline():
                    psutil.Process(proc.pid).terminate()  # Deleting chromedriver objects from RAM
            except Exception as e:
                # In case of required permission
                continue
        if os.path.exists('CheckDevice.py'):
            os.remove('CheckDevice.py')
        exit(code=0)
    except KeyboardInterrupt as e:
        # If the interrupted we must try again
        finishing_up()


if __name__ == "__main__":
    main()
