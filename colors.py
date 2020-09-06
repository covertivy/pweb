#!/bin/python3
class Colors:
    """
    common use of the class methods:
        print(Colors.color(0, 0, 0, "hello"))
        # or
        print(Colors.BOLD + "hello" + Colors.ENDC)
        # or
        print(f"{Colors.UNDERLINE}hello{Colors.ENDC}")
    """

    ENDC = "\033[0m"  # back to normal
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\u001b[37m"

    BRIGHT_BLACK = "\u001b[30;1m"
    BRIGHT_RED = "\u001b[31;1m"
    BRIGHT_GREEN = "\u001b[32;1m"
    BRIGHT_YELLOW = "\u001b[33;1m"
    BRIGHT_BLUE = "\u001b[34;1m"
    BRIGHT_MAGENTA = "\u001b[35;1m"
    BRIGHT_CYAN = "\u001b[36;1m"
    BRIGHT_WHITE = "\u001b[37;1m"

    @staticmethod
    def color(red, green, blue, text):
        """
        function paints the text
        :param red: int, 0-255
        :param green: int, 0-255
        :param blue: int, 0-255
        :param text: string
        :return: painted text
        """
        return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(
            red, green, blue, text
        )

