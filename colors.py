class Colors:
    """
    common use of the class methods:
        print(Colors.color(0, 0, 0, "hello"))
        # or
        print(Colors.BOLD + "hello" + Colors.ENDC)
        # or
        print(f"{Colors.UNDERLINE}hello{Colors.ENDC}")
    """

    RED = '\033[91m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    NAVY = '\033[96m'
    ENDC = '\033[0m'  # back to normal
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
        return "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(red, green, blue, text)