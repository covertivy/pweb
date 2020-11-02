#!/usr/bin/python3
#!/usr/bin/python3
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
PLUGINS_FOLDER = 'plugins' # local plugin folder name.
PLUGIN_PATH_SECTION = "plugins" # the config file section in which the plugins are stored.
GENERIC_FUNC_NAME = 'check' # name of the generic function each file has to implement.
CHECK_DEVICE_NAME = 'CheckDevice' # The name of the Check Device.
CONFIG_PATHS_KEY = 'paths'

COLOR_MANAGER = colors.Colors()


def fetch_plugins():
    """
    this function obtains the config file containing the path of each plugin,
    parses it into a list of plugin paths and returns it. while also handeling errors.
    :return: plugin_path_list (list of paths)
    """

    # Begin parsing plugin config file.
    cfg_parser = ConfigParser()

    # Check if config file exists.
    if not os.path.exists(CONFIG_FILE_PATH):
        raise Exception('Config file "{CONFIG_FILE_PATH}" was not found!')
    # Read config file:
    cfg_parser.read(CONFIG_FILE_PATH)

    # Check if the paths are stored in the correct section inside of the config file.
    # For more information check out "https://docs.python.org/3/library/configparser.html"
    if PLUGIN_PATH_SECTION not in cfg_parser.sections():
        raise Exception(
            f'Section "{PLUGIN_PATH_SECTION}" was not found in config file "{CONFIG_FILE_NAME}"'
        )

    # Check if the mandatory key CONFIG_PATHS_KEY exists inside the desired section.
    # For more information check out "https://docs.python.org/3/library/configparser.html"
    if CONFIG_PATHS_KEY not in cfg_parser[PLUGIN_PATH_SECTION]:
        raise Exception(
            f'Key "{CONFIG_PATHS_KEY}" was not found in section "{PLUGIN_PATH_SECTION}"'
        )

    # Save paths from the config file.
    plugin_path_list = cfg_parser[PLUGIN_PATH_SECTION][CONFIG_PATHS_KEY].split(",\n")

    # Check if there are paths inside the section under the key CONFIG_PATHS_KEY.
    if len(plugin_path_list) == 0:
        raise Exception(
            f'No plugin paths were found in config file "{CONFIG_FILE_NAME}"'
        )

    # Print fancy plugin fetcher with color and cool stuff.
    print(
        COLOR_MANAGER.GREEN
        + COLOR_MANAGER.UNDERLINE
        + COLOR_MANAGER.BOLD
        + "Fetching plugins:"
        + COLOR_MANAGER.ENDC
    )
    for path in plugin_path_list:
        print(
            "\t["
            + COLOR_MANAGER.GREEN
            + "+"
            + COLOR_MANAGER.ENDC
            + "] "
            + COLOR_MANAGER.GREEN
            + path
            + COLOR_MANAGER.ENDC
        )

    return plugin_path_list


def generate_check_device():
    """
    this function writes to the checker.py file the plugins that were collected
    :return: none
    """
    try:
        paths = fetch_plugins() # get all paths from the plugin config file.
    except Exception as e: # Make sure no errors exist.
        COLOR_MANAGER.print_error(e)

    checker = open(f"{CHECK_DEVICE_NAME}.py", "w") # Generate a new check device.

    # Get each plugin file name so we can import each one into the check device.
    plugins_names = [path.split("/")[-1].split(".")[0] for path in paths]

    # Write all the plugin imports into the check device.
    for plugin in plugins_names:
        checker.write(f"import {PLUGINS_FOLDER}.{plugin} as {plugin}\n")

    # Store all plugin functions in a list.
    checker.write(f'\nALL_FUNCS = [{plugins_names[0]}.{GENERIC_FUNC_NAME}')
    for plugin in plugins_names[1:]:
        checker.write(f", {plugin}.{GENERIC_FUNC_NAME}")
    
    checker.write("]\n")
    checker.close()
