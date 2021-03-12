#!/usr/bin/python3
from Classes import Data
import FlagManager
import PluginManager
import AddressManager
import PageManager
import VulnerabilityManager
from colors import COLOR_MANAGER, startup
import datetime
import os
import psutil


def get_data() -> Data:
    """
    Function gets the Data object to a initial check stage
    @return: Data object that ready for the Page manager
    """
    data = FlagManager.get_final_args(FlagManager.parse_args())  # Get arguments from command line.
    if data.verbose:
        # Print startup logo and current time.
        print(startup())
        print(f"{COLOR_MANAGER.GREEN}Started on: {datetime.datetime.now()}{COLOR_MANAGER.ENDC}")
    AddressManager.set_target(data)
    return data


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


def signal_handler():
    """
    Function wait for a key interrupt and killing the process safely
    @return: None
    """
    COLOR_MANAGER.print_warning("You have decided to close the process, please wait few seconds...\n", "\n\t")
    for proc in psutil.process_iter():
        try:
            if "chrome" in proc.name() and '--test-type=webdriver' in proc.cmdline():
                psutil.Process(proc.pid).terminate()  # Deleting chromedriver objects from RAM
        except Exception as e:
            # In case of required permission
            continue


def main():
    """
    Function connects the different managers together
    @return: None
    """
    os.system("color")  # Without it, the COLOR_MANAGER won't work.
    try:
        data = get_data()  # Get data through flag manager, address manager and page manager.
        if data.port == 0:
            # If the user asked for ports scan (-P) there is no need to continue the run.
            exit()
        print_data(data)
        PageManager.logic(data)  # Get all pages from website.
        exit(0)
        PluginManager.generate_check_device()  # Generate Check Device in our directory.
        VulnerabilityManager.logic(data)
        print(COLOR_MANAGER.ENDC)
    except KeyboardInterrupt as e:
        # The user pressed ctrl+c
        signal_handler()
    except Exception as e:
        if len(e.args) == 2:
            COLOR_MANAGER.print_error(str(e.args[0]), str(e.args[1]))
        else:
            COLOR_MANAGER.print_error(str(e))
    finally:
        if os.path.exists('CheckDevice.py'):
            os.remove('CheckDevice.py')
        exit(code=0)


if __name__ == "__main__":
    main()
