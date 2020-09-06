#!/usr/bin/python3
import requests
import os
import colors
import get_plugins
from get_pages import Pages
from parse_args import parse_args

COLOR_MANAGER = colors.Colors()


def main(
    ip: str,
    port: int,
    ALL_PORTS: bool,
    url: str,
    IS_URL: bool,
    max_page_num: int,
    username: str,
    password: str,
    output_folder: str,
):
    # Check if url is up.
    try:
        response = requests.get(url)
    except Exception as timeout:
        print(
            COLOR_MANAGER.RED
            + "ERROR: "
            + COLOR_MANAGER.ENDC
            + "Timeout! host may be down or may not exist!"
        )
        print(COLOR_MANAGER.BRIGHT_YELLOW + "Exiting..." + COLOR_MANAGER.ENDC)
        exit(code=-1)
    try:
        plugin_path_list = get_plugins.get_files()  # Gets the list of plugin paths
        pages = Pages(url)  # Gets the list of pages
        get_plugins.write_checker(
            plugin_path_list
        )  # If there is no problem with the plugins
        # (The write_checker() function doesn't need exceptions)
        print(
            COLOR_MANAGER.BOLD
            + COLOR_MANAGER.UNDERLINE
            + "Start checking:"
            + COLOR_MANAGER.ENDC
        )
        import checker  # Even if the file was removed the code will still compile

        checker.main(pages)  # Start the checker from here will catch further exceptions

        # Delete temporary checker file.
        os.remove("checker.py")
    except Exception as e:
        # Print each error in a fancy format.
        print(COLOR_MANAGER.RED + "ERROR: " + COLOR_MANAGER.ENDC, end="")
        print(e)


if __name__ == "__main__":
    args = parse_args()  # Get arguments from command line.
    # TODO: send parsed args to main and check them in parse_args file.
    main()
