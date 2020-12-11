#!/usr/bin/python3
import Data
import FlagManager
import PluginManager
import AddressManager
import PageManager
import VulnerabilityManager
import datetime
from colors import COLOR_MANAGER

LOGO = """                           __        
                          /\ \       
 _____   __  __  __     __\ \ \____  
/\ '__`\/\ \/\ \/\ \  /'__`\ \ '__`\ 
\ \ \L\ \ \ \_/ \_/ \/\  __/\ \ \L\ \\
 \ \ ,__/\ \___x___/'\ \____\\\ \_,__/
  \ \ \/  \/__//__/   \/____/ \/___/ 
   \ \_\                             
    \/_/                             """


def print_startup():
    """
    Print majestic logo.
    """
    for char in LOGO:
        print(COLOR_MANAGER.rand_color() + char, end="")
    print(COLOR_MANAGER.ENDC + "\n")
    print(
        f"{COLOR_MANAGER.GREEN}Started on: {datetime.datetime.now()}{COLOR_MANAGER.ENDC}"
    )


def get_data() -> Data.Data:
    """
    Function sets the Data object variables for the check process
    :return: basic Data object
    """
    data = FlagManager.get_final_args(
        FlagManager.parse_args()
    )  # Get arguments from command line.
    if data.verbose:
        print_startup()  # Print startup logo and current time.
    #AddressManager.set_target(data)
    return data


def print_data(data: Data.Data):
    """
    Function prints the inserted data
    """
    print(f"\n{COLOR_MANAGER.PINK + COLOR_MANAGER.HEADER}Inserted data:{COLOR_MANAGER.ENDC}")
    for line in str(data).split("\n"):
        print(f"\t[{COLOR_MANAGER.PINK}*{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.PINK}{line}{COLOR_MANAGER.ENDC}")
    print(COLOR_MANAGER.ENDC)


def main():
    try:
        data = get_data()  # Get data through flag manager, address manager and page manager.
        if type(data.port) is not int:
            # If the user asked for ports scan (-P) there is no need to continue the run
            exit()
        print_data(data)
        PageManager.logic(data)  # Get all pages from website
        PluginManager.generate_check_device()  # Generate Check Device in our directory.
        VulnerabilityManager.logic(data)
        print(COLOR_MANAGER.ENDC)
    except Exception as e:
        if len(e.args) == 2:
            COLOR_MANAGER.print_error(str(e.args[0]), str(e.args[1]))
        else:
            COLOR_MANAGER.print_error(str(e))
    finally:
        # os.remove('CheckDevice.py')
        exit(code=0)


if __name__ == "__main__":
    main()
