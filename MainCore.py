#!/usr/bin/python3
from Data import Data
import FlagManager
import PluginManager
import OutputManager
import VulnerabilityManager
import os
import colors


LOGO = """                           __    
                          /\ \       
 _____   __  __  __     __\ \ \____  
/\ '__`\/\ \/\ \/\ \  /'__`\ \ '__`\ 
\ \ \L\ \ \ \_/ \_/ \/\  __/\ \ \L\ \\
 \ \ ,__/\ \___x___/'\ \____\\\ \_,__/
  \ \ \/  \/__//__/   \/____/ \/___/ 
   \ \_\                             
    \/_/   """


COLOR_MANAGER = colors.Colors()


def get_plugin_funcs():
    PluginManager.generate_check_device() # Generate Check Device in our directory.
    if os.path.exists(os.getcwd() + f'\{PluginManager.CHECK_DEVICE_NAME}.py'): # Check if it actually exists.
        try:
            import CheckDevice # Try to import.
        except ModuleNotFoundError as e: # Error in Check Device plugin imports.
            COLOR_MANAGER.print_error(f'Plugin files missing from the specified plugin folder!\n\t( {e} )\nAborting...')
            os.remove(os.getcwd() + f'\{PluginManager.CHECK_DEVICE_NAME}.py')
            exit()
        # Catch any other error (could be function 'check' does not exist in a plugin module)
        except Exception as e:
            COLOR_MANAGER.print_error(f'ERROR!\n\t( {e} )\nAborting...')
            exit()

        return CheckDevice.ALL_FUNCS

    else: # Check file does not exist.
        COLOR_MANAGER.print_error(f'Check device does not exist!\n\t( {PluginManager.CHECK_DEVICE_NAME}.py )\nAborting...')
        exit()


def get_data():
    data = FlagManager.get_final_args(FlagManager.parse_args())  # Get arguments from command line.
    
    # TODO: update the data through page manager and address manager.

    return data


def main():
    # print magestic logo.
    os.system("clear")
    for char in LOGO:
        print(COLOR_MANAGER.randcolor() + char, end='')
    print(COLOR_MANAGER.ENDC)

    # Get data through flag manager, address manager and page manager.
    data = get_data()
    print(data)

    plugin_funcs = get_plugin_funcs() # Get all plugin functions from the Check Device.
    for func in plugin_funcs:
        func('halo')
    # TODO:
    # Plugin Manager actions
    # Vulnerabilities Manager actions (needs data)
    # Output Manager actions (needs data)
    os.remove(f'{os.getcwd()}/{PluginManager.CHECK_DEVICE_NAME}.py')

if __name__ == "__main__":
    main()
