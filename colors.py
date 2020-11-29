#!/usr/bin/python3
import random


def rgb(red: int, green: int, blue: int):
    """
    function paints the text
    :param red: int, 0-255
    :param green: int, 0-255
    :param blue: int, 0-255
    :return: paint format
    """
    return "\033[38;2;{};{};{}m".format(red, green, blue)


class Colors:
    """
    common use of the class methods:
        print(Colors.rgb(0, 0, 0) + "hello")
        # or
        print(Colors.BOLD + "hello" + Colors.ENDC)
        # or
        print(f"{Colors.UNDERLINE}hello{Colors.ENDC}")
    """

    ENDC = "\033[0m"  # back to normal
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HEADER = BOLD + UNDERLINE

    RED = rgb(255, 0, 0)
    GREEN = rgb(0, 255, 0)
    ORANGE = rgb(255, 128, 0)
    BLUE = rgb(0, 128, 255)
    LIGHT_GREEN = rgb(0, 255, 128)
    PURPLE = rgb(128, 0, 255)
    CYAN = rgb(0, 255, 255)
    TURQUOISE = rgb(64, 224, 208)
    WHITE = rgb(255, 255, 255)
    BLACK = rgb(0, 0, 0)
    YELLOW = rgb(255, 255, 0)
    PINK = rgb(255, 0, 255)

    BOLD_RED = RED + BOLD
    BOLD_GREEN = GREEN + BOLD
    BOLD_ORANGE = ORANGE + BOLD
    BOLD_BLUE = BLUE + BOLD
    BOLD_LIGHT_GREEN = LIGHT_GREEN + BOLD
    BOLD_PURPLE = PURPLE + BOLD
    BOLD_CYAN = CYAN + BOLD
    BOLD_TURQUOISE = TURQUOISE + BOLD
    BOLD_WHITE = WHITE + BOLD
    BOLD_BLACK = BLACK + BOLD
    BOLD_YELLOW = YELLOW + BOLD
    BOLD_PINK = PINK + BOLD

    @staticmethod
    def rgb(red: int, green: int, blue: int):
        """
        function paints the text
        :param red: int, 0-255
        :param green: int, 0-255
        :param blue: int, 0-255
        :return: paint format
        """
        return rgb(red, green, blue)

    @staticmethod
    def rand_color():
        return rgb(
            random.choice(range(255)),
            random.choice(range(255)),
            random.choice(range(255)),
        )

    @staticmethod
    def print_warning(warning: str = "WARNING!", begins_with: str = ""):
        print(
            begins_with
            + "["
            + Colors.BOLD_YELLOW
            + "!"
            + Colors.ENDC
            + "] "
            + Colors.BOLD_YELLOW
            + warning
            + Colors.ENDC
        )

    @staticmethod
    def print_error(error: str = "ERROR!"):
        print(
            "["
            + Colors.BOLD_RED
            + "!"
            + Colors.ENDC
            + "] "
            + Colors.BOLD_RED
            + error
            + Colors.ENDC
        )


COLOR_MANAGER = Colors()
