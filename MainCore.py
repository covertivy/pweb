#!/usr/bin/python3
from Data import Data
import FlagManager
import PluginManager
import OutputManager
import VulnerabilityManager
import os
from colors import COLOR_MANAGER


LOGO = """                           __    
                          /\ \       
 _____   __  __  __     __\ \ \____  
/\ '__`\/\ \/\ \/\ \  /'__`\ \ '__`\ 
\ \ \L\ \ \ \_/ \_/ \/\  __/\ \ \L\ \\
 \ \ ,__/\ \___x___/'\ \____\\\ \_,__/
  \ \ \/  \/__//__/   \/____/ \/___/ 
   \ \_\                             
    \/_/   """


def get_plugin_funcs():
    PluginManager.generate_check_device() # Generate Check Device in our directory.
    if os.path.exists(os.getcwd() + f'/{PluginManager.CHECK_DEVICE_NAME}.py'): # Check if it actually exists.
        try:
            from CheckDevice import ALL_FUNCS  # Try to import.
        except ModuleNotFoundError as e:  # Error in Check Device plugin imports.
            COLOR_MANAGER.print_error(f'Plugin files missing from the specified plugin folder!\n\t( {e} )\nAborting...')
            exit()
        # Catch any other error (could be function 'check' does not exist in a plugin module)
        except Exception as e:
            COLOR_MANAGER.print_error(f'ERROR!\n\t( {e} )\nAborting...')
            exit()

        return ALL_FUNCS  # Get and return the list of all plugin functions from Check Device.

    else:  # Check file does not exist.
        COLOR_MANAGER.print_error(f'Check device does not exist!\n\t( {PluginManager.CHECK_DEVICE_NAME}.py)\nAborting...')
        exit()


def get_data():
    data = FlagManager.get_final_args(FlagManager.parse_args())  # Get arguments from command line.
    
    # TODO: update the data through page manager and address manager.

    return data


def main():
    # print magestic logo.
    for char in LOGO:
        print(COLOR_MANAGER.randcolor() + char, end='')
    print(COLOR_MANAGER.ENDC + '\n')

    # Get data through flag manager, address manager and page manager.
    data = get_data()
    print(data, end="\n\n")

    plugin_funcs = get_plugin_funcs()  # Get all plugin functions from the Check Device.
    for func in plugin_funcs:
        func(data)  # Should be pages received from the data object.

    print("\n", end="")

    # TODO:
    # Vulnerabilities Manager actions (needs data)
    # Output Manager actions (needs data)


if __name__ == "__main__":
    main()
