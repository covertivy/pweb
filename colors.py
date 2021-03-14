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
    Function paints the text.
    @param red (int): Red value of RGB 0-255.
    @param green (int): Green value of RGB 0-255.
    @param blue (int): Blue value of RGB 0-255.
    @returns str: ANSI color value string.
    """
    return "\033[38;2;{};{};{}m".format(red, green, blue)


def validate_parameter(param: tuple, strlen: int): 
    if len(param) != 3:
        return False
    type_bool: bool = all((type(param[0]) == int, type(param[1]) == int, type(param[2]) == str))
    size_bool: bool = all((param[0] >= 0, param[1] > 0, param[0] < param[1], param[1] <= strlen))
    return type_bool and size_bool
    


class Colors:
    ENDC = "\033[0m"  # back to normal
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HEADER = BOLD + UNDERLINE

    RED = rgb(255, 0, 0)
    GREEN = rgb(0, 255, 0)
    ORANGE = rgb(255, 128, 0)
    BLUE = rgb(0, 128, 255)
    LIGHT_BLUE = rgb(51, 153, 255)
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
        Function paints the text.
        @param red (int): Red value of RGB 0-255.
        @param green (int): Green value of RGB 0-255.
        @param blue (int): Blue value of RGB 0-255.
        @returns str: ANSI color value string.
        """
        return rgb(red, green, blue)


    @staticmethod
    def rand_color():
        """
        Function paints the text in random color
        @returns str: Random ANSI color value string.
        """
        return rgb(
            random.choice(range(255)),
            random.choice(range(255)),
            random.choice(range(255)))


    @staticmethod
    def print_success(success: str = "SUCCESS!", begins_with: str = "", ends_with: str = ""):
        """
        Function prints a given success message.
        @param success: The specified message.
        @param begins_with: Optional string to start with.
        @returns None.
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
            + Colors.ENDC
            + ends_with)
    

    @staticmethod
    def print_information(info: str, begins_with: str = "", ends_with: str = ""):
        """
        Function prints a given success message.
        @param success: The specified message.
        @param begins_with: Optional string to start with.
        @returns None.
        """
        print(
            begins_with
            + Colors.ENDC
            + "["
            + Colors.LIGHT_BLUE
            + "?"
            + Colors.ENDC
            + "] "
            + Colors.LIGHT_BLUE
            + info
            + Colors.ENDC
            + ends_with)
    

    @staticmethod
    def print_warning(warning: str = "WARNING!", begins_with: str = "", ends_with: str = ""):
        """
        Function prints a specified warning.
        @param warning: The specified warning.
        @param begins_with: Optional string to start with.
        @returns None.
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
            + Colors.ENDC
            + ends_with)


    @staticmethod
    def print_error(error: str = "ERROR!", begins_with: str = "", ends_with: str = ""):
        """
        Function prints a specified error.
        @param error: The specified error.
        @param begins_with: Optional string to start with.
        @returns None.
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
            + Colors.ENDC
            + ends_with)


    @staticmethod
    def modify_string(input_str: str, parameters: list):
        """
        This function receives a string to modify and the parameters to modify it with.
        Each parameter is a tuple 3 values long, the first two are start and stop indexes for the wanted modification.
        ? Important: Please make sure that you send a *LIST* of tuples and not a single tuple.
        ? Important Note: We strongly advise you to use the included ANSI modifications given in this class.
        ! PLEASE NOTE: You cannot specify colliding indexes!
        !   For example: 
        !       (0, 5) and (2, 10) will not work correctly! if you wish to combine several modifications you can do so by specifying them like so:
                    > COLOR_MANAGER.modify_string("abcdefg", [(0, 4, COLOR_MANAGER.GREEN + COLOR_MANAGER.BOLD)])
                    > This will result in a bold green `abcd` and the rest as normal text.
        ! PLEASE NOTE: the start and stop indexes are not direct indexes but are used like the string indices in python,
        !   Which means that the stop index is not included in the final string.
        !   For example:
        !       in the string "hello, world!", to modify the word `hello` we will use the indexes (0, 5).
        
        @param input_str (str): The string to modify with the given parameters.
        @param parameters (list): The parameters to modify the string with, each parameter is a tuple of:
        >   (begin_index : int, stop_index : int, ansi_modification : str).
        @returns str: The modified string with the valid changes made to it, if for some reason there are some missing changes please read the description. 
        """
        # Get list of all valid parameters.
        valid_params = [param for param in parameters if validate_parameter(param, len(input_str))]
        if len(valid_params) == 0:
            return input_str
        
        # Get lists of all the needed indexes and sort them from last to first.
        endc_indexes = list(set([param[1] for param in valid_params]))
        endc_indexes.sort(reverse=True)
        mod_indexes = list(set([(param[0], param[2]) for param in valid_params]))
        mod_indexes.sort(key=lambda x: x[0], reverse=True)
        
        output_str = Colors.ENDC
        ansi_to_add = ""

        prev_index = len(input_str)
        index = 0
        skip_endc = False

        modi = 0
        endci = 0
        while modi < len(valid_params) or endci < len(valid_params):
            mod_index = None
            endc_index = None
            if modi < len(valid_params):
                mod_index = mod_indexes[modi] # Current modification parameter.
            if endci < len(valid_params):
                endc_index = endc_indexes[endci] # Current endc parameter.
            
            if mod_index is not None and endc_index is not None:
                # Check which one should go before the other.
                if mod_index[0] > endc_index:
                    index = mod_index[0]
                    ansi_to_add = mod_index[1]
                    modi += 1
                elif mod_index[0] < endc_index:
                    if not skip_endc:
                        index = endc_index
                        ansi_to_add = Colors.ENDC
                        endci += 1
                    skip_endc = False
                else:
                    # Both need to be used and therefor we must put the endc first so the color will continue.
                    index = endc_index
                    ansi_to_add = Colors.ENDC + mod_index[1]
                    skip_endc = True
                    modi += 1
                    endci += 1
            elif mod_index is not None:
                index = mod_index[0]
                ansi_to_add = mod_index[1]
                modi += 1
            elif endc_index is not None:
                index = endc_index
                ansi_to_add = Colors.ENDC
                endci += 1
            
            # Append the modified text to the output string.
            output_str = ansi_to_add + input_str[index: prev_index] + output_str
            prev_index = index
        
        if index != 0:
            # If we did not reach the beginning of the string we need to add it.
            output_str = input_str[0: prev_index] + output_str
        
        return output_str


COLOR_MANAGER = Colors()  # Colors instance


def startup():
    """
    Function prints majestic logo.
    @returns None.
    """
    logo = ""
    for char in LOGO:
        logo += COLOR_MANAGER.rand_color() + char
    logo += COLOR_MANAGER.ENDC + "\n"
    return logo
