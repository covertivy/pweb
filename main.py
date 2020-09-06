#!/usr/bin/python
import os
import colors
import get_plugins
from get_pages import Pages

COLOR_MANAGER = colors.Colors()


def main(url="http://192.168.56.101//dvwa/"):
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
    main()
