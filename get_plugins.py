#!/usr/bin/python
import os
import colors
from configparser import ConfigParser

THIS_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)  # Get relative path to our folder.
CONFIG_FILE_NAME = "pluginconfig.ini"
CONFIG_FILE_PATH = os.path.join(
    THIS_FOLDER, CONFIG_FILE_NAME
)  # Create path of config file. (name can be changed)
PLUGIN_PATH_SECTION = "plugins"
COLOR_MANAGER = colors.Colors()


def get_files():
    """
    this function obtains the config file containing the path of each plugin,
    parses it into a list of plugin paths and returns it. while also handeling errors.
    :return: plugin_path_list (list of paths)
    """

    # Begin parsing plugin config file.
    cfg_parser = ConfigParser()

    # Check if config file exists.
    if not os.path.isfile(CONFIG_FILE_PATH):
        raise Exception('Config file "{}" was not found!'.format(CONFIG_FILE_PATH))
    # Read config file:
    cfg_parser.read(CONFIG_FILE_PATH)

    # Check if the paths are stored in the correct section inside of the config file.
    # For more information check out "https://docs.python.org/3/library/configparser.html"
    if PLUGIN_PATH_SECTION not in cfg_parser.sections():
        raise Exception(
            'Section "{}" was not found in config file "{}"'.format(
                PLUGIN_PATH_SECTION, CONFIG_FILE_NAME
            )
        )

    # Check if the mandatory key "paths" exists inside the desired section.
    # For more information check out "https://docs.python.org/3/library/configparser.html"
    if "paths" not in cfg_parser[PLUGIN_PATH_SECTION]:
        raise Exception(
            'Key "paths" was not found in section "{}"'.format(PLUGIN_PATH_SECTION)
        )

    plugin_path_list = cfg_parser[PLUGIN_PATH_SECTION]["paths"].split(",\n")

    # Check if there are paths inside the section under the key "paths".
    if len(plugin_path_list) == 0:
        raise Exception(
            'No plugin paths were found in config file "{}"'.format(CONFIG_FILE_NAME)
        )

    # Print fancy plugin fetcher with color and cool stuff.
    print(COLOR_MANAGER.GREEN + COLOR_MANAGER.UNDERLINE + COLOR_MANAGER.BOLD + "Fetching plugins:" + COLOR_MANAGER.ENDC)
    for path in plugin_path_list:
        print("\t[" + COLOR_MANAGER.GREEN + "+" + COLOR_MANAGER.ENDC + "] "
                    + COLOR_MANAGER.GREEN + path + COLOR_MANAGER.ENDC)

    return plugin_path_list


def write_checker(plugin_path_list):
    """
    this function writes to the checker.py file the plugins that were collected
    :param plugin_path_list: list of plugins paths
    :return: none
    """
    checker = open("checker.py", "w")
    checker.write("")  # Deleting the file's content
    checker.close()

    plugins_names = [path.split("/")[-1].split(".")[0] for path in plugin_path_list]

    checker = open("checker.py", "a")
    for plugin in plugins_names:
        checker.write(f"import {PLUGIN_PATH_SECTION}.{plugin} as {plugin}\n")
    checker.write("\n\ndef main(pages):\n")
    for plugin in plugins_names:
        checker.write(f"\t{plugin}.check(pages)\n")
    checker.write("\n")
    checker.close()
