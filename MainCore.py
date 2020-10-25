#!/usr/bin/python3
from Data import Data
import FlagManager
import PluginManager
import OutputManager
import VulnerabilityManager
import colors

COLOR_MANAGER = colors.Colors()


def main():
    # print magestic logo.
    print(COLOR_MANAGER.BRIGHT_GREEN + "██████╗ ██╗    ██╗███████╗██████╗ \n██╔══██╗██║    ██║██╔════╝██╔══██╗\n██████╔╝██║ █╗ ██║█████╗  ██████╔╝\n██╔═══╝ ██║███╗██║██╔══╝  ██╔══██╗\n██║     ╚███╔███╔╝███████╗██████╔╝\n╚═╝      ╚══╝╚══╝ ╚══════╝╚═════╝ \n" + COLOR_MANAGER.ENDC)

    # TODO:
    # data = Flag Manager's return object
    # Plugin Manager actions
    # Vulnerabilities Manager actions (needs data)
    # Output Manager actions (needs data)


if __name__ == "__main__":
    main()
