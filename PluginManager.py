#!/usr/bin/python3
import os
from colors import COLOR_MANAGER
from configparser import ConfigParser
from Classes import Manager, Data

CHECK_DEVICE_NAME = "CheckDevice"  # The name of the Check Device.


class PluginManager(Manager):
    def __init__(self):
        self.__THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))  # Get relative path to our folder.
        self.__CONFIG_FILE_NAME = "pluginconfig.ini"  # Plugin configuration file name.
        self.__CONFIG_FILE_PATH = os.path.join(self.__THIS_FOLDER, self.__CONFIG_FILE_NAME)  # Create path of config file.
        self.__PLUGINS_FOLDER = "plugins"  # Local plugin folder name.
        self.__PLUGIN_PATH_SECTION = "plugins"  # The config file section in which the plugins are stored.
        self.__GENERIC_FUNC_NAME = "check"  # The name of the generic function each file has to implement.
        self.__CONFIG_PATHS_KEY = "paths"  # The name of the paths key in the config file.

    def __fetch_plugins(self):
        """
        This function obtains the config file containing the path of each plugin,
        parses it into a list of plugin paths and returns it, while also handling errors.
        
        @return: plugin_path_list (list of paths).
        @rtype: list
        """
        # Begin parsing plugin config file.
        cfg_parser = ConfigParser()

        # Check if config file exists.
        if not os.path.exists(self.__CONFIG_FILE_PATH):
            raise Exception(f'Config file "{self.__CONFIG_FILE_PATH}" was not found!', "\t")
        # Read config file.
        cfg_parser.read(self.__CONFIG_FILE_PATH)

        # Check if the paths are stored in the correct section inside of the config file.
        # For more information check out "https://docs.python.org/3/library/configparser.html".
        if self.__PLUGIN_PATH_SECTION not in cfg_parser.sections():
            raise Exception(f'Section "{self.__PLUGIN_PATH_SECTION}" was not found in config file "{self.__CONFIG_FILE_NAME}"', "\t")

        # Check if the mandatory key CONFIG_PATHS_KEY exists inside the desired section.
        # For more information check out "https://docs.python.org/3/library/configparser.html".
        if self.__CONFIG_PATHS_KEY not in cfg_parser[self.__PLUGIN_PATH_SECTION]:
            raise Exception(f'Key "{self.__CONFIG_PATHS_KEY}" was not found in section "{self.__PLUGIN_PATH_SECTION}"', "\t")

        # Save paths from the config file.
        plugin_path_list = cfg_parser[self.__PLUGIN_PATH_SECTION][self.__CONFIG_PATHS_KEY].split(",\n")

        # Check if there are paths inside the section under the key CONFIG_PATHS_KEY.
        if len(plugin_path_list) == 0:
            raise Exception(f'No plugin paths were found in config file "{self.__CONFIG_FILE_NAME}"', "\t")

        # Print fancy plugin fetcher with color and cool stuff.
        print(
            COLOR_MANAGER.LIGHT_GREEN
            + COLOR_MANAGER.HEADER
            + "Fetching plugins:"
            + COLOR_MANAGER.ENDC)

        # Check each plugin in the plugin config file.
        index = 0
        while index < len(plugin_path_list):
            path = plugin_path_list[index]

            # Check if plugin exists in specified path.
            if os.path.isfile(path):
                # Check if plugin is a python file.
                if not path.endswith(".py"):
                    COLOR_MANAGER.print_error(f'Plugin "{path}" is not a python file! (ignoring...)', "\t")
                    plugin_path_list.pop(index)
                else:
                    print(f"\t[{COLOR_MANAGER.LIGHT_GREEN}+{COLOR_MANAGER.ENDC}] "
                          f"{COLOR_MANAGER.LIGHT_GREEN}{path}{COLOR_MANAGER.ENDC}")
                    index += 1
            else:
                COLOR_MANAGER.print_warning(f'Plugin path "{path}" does not exist! (ignoring...)', "\t")
                plugin_path_list.remove(path)

        print(COLOR_MANAGER.ENDC)
        return plugin_path_list

    def __generate_check_device(self, paths):
        """
        This function generates the `CheckDevice.py` file and imports the plugins that were collected,
        then stores their functions in a list.

        @return None.
        """
        COLOR_MANAGER.print_information(f'Creating Check Device "{CHECK_DEVICE_NAME}.py"...', "\t")
        checker = open(f"{CHECK_DEVICE_NAME}.py", "w")  # Generate a new check device.
        # Get each plugin file name so we can import each one into the check device.
        plugins_names = [path.split("/")[-1].split(".")[0] for path in paths]
        # Write all the plugin imports into the check device.
        for plugin in plugins_names:
            checker.write(f"import {self.__PLUGINS_FOLDER}.{plugin} as {plugin}\n")
        # Store all plugin functions in a list.
        checker.write(f"\nALL_FUNCS = [{plugins_names[0]}.{self.__GENERIC_FUNC_NAME}")
        for plugin in plugins_names[1:]:
            checker.write(f", {plugin}.{self.__GENERIC_FUNC_NAME}")

        checker.write("]\n")
        checker.close()
        COLOR_MANAGER.print_success(f'Successfully Created Check Device file "{CHECK_DEVICE_NAME}.py"!', "\t", "\n")

    def logic(self, data: Data):
        """
        This function gets the paths of the plugins from the configuration file and generates a check device.

        @param data: The data object of the program.
        @type data: Data
        @return: None.
        """
        paths: list = self.__fetch_plugins()  # Get all the paths from the plugin config file.
        self.__generate_check_device(paths)
