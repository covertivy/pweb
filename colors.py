#!/usr/bin/python3
import random

LOGO = r"                           __" + "\n" \
       r"                          /\ \   " + "\n" \
       r" _____   __  __  __     __\ \ \____" + "\n" \
       r"/\ '__`\/\ \/\ \/\ \  /'__`\ \ '__`\ " + "\n" \
       r"\ \ \L\ \ \ \_/ \_/ \/\  __/\ \ \L\ \ " + "\n" \
       r" \ \ ,__/\ \___x___/'\ \____\\ \_,__/" + "\n" \
       r"  \ \ \/  \/__//__/   \/____/ \/___/ " + "\n" \
       r"   \ \_\ " + "\n"\
       r"    \/_/"


def rgb(red: int, green: int, blue: int):
    """
    Function paints the text
    @param red: int, 0-255
    @param green: int, 0-255
    @param blue: int, 0-255
    @return: Paint format
    """
    return "\033[38;2;{};{};{}m".format(red, green, blue)


class Colors:
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
    def rgb(red: int, green: int, blue: int) -> str:
        """
        Function paints the text
        @param red: int, 0-255
        @param green: int, 0-255
        @param blue: int, 0-255
        @return: Paint format
        """
        return rgb(red, green, blue)

    @staticmethod
    def rand_color() -> str:
        """
        Function paints the text in random color
        @return: Paint format
        """
        return rgb(
            random.choice(range(255)),
            random.choice(range(255)),
            random.choice(range(255)))

    @staticmethod
    def print_warning(warning: str = "WARNING!", begins_with: str = ""):
        """
        Function prints a specified warning
        @param warning: The specified warning
        @param begins_with: Optional string to start with
        @return: None
        """
        print(
            begins_with
            + Colors.ENDC
            + "["
            + Colors.BOLD_YELLOW
            + "!"
            + Colors.ENDC
            + "] "
            + Colors.BOLD_YELLOW
            + warning
            + Colors.ENDC)

    @staticmethod
    def print_error(error: str = "ERROR!", begins_with: str = ""):
        """
        Function prints a specified error
        @param error: The specified error
        @param begins_with: Optional string to start with
        @return: None
        """
        print(
            begins_with
            + Colors.ENDC
            + "["
            + Colors.BOLD_RED
            + "!"
            + Colors.ENDC
            + "] "
            + Colors.BOLD_RED
            + error
            + Colors.ENDC)

    @staticmethod
    def print_success(success: str = "SUCCESS!", begins_with: str = ""):
        """
        Function prints a specified success message
        @param success: The specified message
        @param begins_with: Optional string to start with
        @return: None
        """
        print(
            begins_with
            + Colors.ENDC
            + "["
            + Colors.BOLD_GREEN
            + "!"
            + Colors.ENDC
            + "] "
            + Colors.BOLD_GREEN
            + success
            + Colors.ENDC)


COLOR_MANAGER = Colors()  # Colors instance


def startup() -> str:
    """
    Function prints majestic logo.
    @return: None
    """
    logo = ""
    for char in LOGO:
        logo += COLOR_MANAGER.rand_color() + char
    logo += COLOR_MANAGER.ENDC + "\n"
    return logo
