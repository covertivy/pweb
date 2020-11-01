#!/usr/bin/python3
from Data import Data
import FlagManager
import PluginManager
import OutputManager
import VulnerabilityManager
import os
import colors


COLOR_MANAGER = colors.Colors()


def get_data():
    data = FlagManager.get_final_args(FlagManager.parse_args())  # Get arguments from command line.
    
    # TODO: update the data through page manager and address manager.

    return data


def main():
    # print magestic logo.
    os.system("clear")
    print(COLOR_MANAGER.BRIGHT_GREEN + """
                           __        
                          /\ \       
 _____   __  __  __     __\ \ \____  
/\ '__`\/\ \/\ \/\ \  /'__`\ \ '__`\ 
\ \ \L\ \ \ \_/ \_/ \/\  __/\ \ \L\ \\
 \ \ ,__/\ \___x___/'\ \____\\\ \_,__/
  \ \ \/  \/__//__/   \/____/ \/___/ 
   \ \_\                             
    \/_/   """ + COLOR_MANAGER.ENDC)
    data = get_data()
    # TODO:
    # Plugin Manager actions
    # Vulnerabilities Manager actions (needs data)
    # Output Manager actions (needs data)


if __name__ == "__main__":
    main()
