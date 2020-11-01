#!/usr/bin/python3
import requests
import os
import colors
import get_plugins
import flag_manager

COLOR_MANAGER = colors.Colors()

def get_data():
    Data = flag_manager.get_final_args(flag_manager.parse_args())  # Get arguments from command line.

def main():
    pass


if __name__ == "__main__":
    
    print(Data)
    # TODO: send parsed args to main and check them in parse_args file.
    # main()
