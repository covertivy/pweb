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


def startup():
    """
    This function prints our majestic logo.
    @return: None.
    """
    logo = ""
    for char in LOGO:
        logo += COLOR_MANAGER.rand_color() + char
    logo += COLOR_MANAGER.ENDC + "\n"
    return logo


class Colors:
    def __init__(self):
        self.ENDC = "\033[0m"  # Clear all ANSI changes.
        self.BOLD = "\033[1m"
        self.UNDERLINE = "\033[4m"
        self.HEADER = self.BOLD + self.UNDERLINE
    
        self.RED = self.rgb(255, 0, 0)
        self.GREEN = self.rgb(0, 255, 0)
        self.ORANGE = self.rgb(255, 128, 0)
        self.BLUE = self.rgb(0, 128, 255)
        self.LIGHT_BLUE = self.rgb(51, 153, 255)
        self.LIGHT_GREEN = self.rgb(0, 255, 128)
        self.PURPLE = self.rgb(128, 0, 255)
        self.CYAN = self.rgb(0, 255, 255)
        self.TURQUOISE = self.rgb(64, 224, 208)
        self.WHITE = self.rgb(255, 255, 255)
        self.BLACK = self.rgb(0, 0, 0)
        self.YELLOW = self.rgb(255, 255, 0)
        self.PINK = self.rgb(255, 0, 255)
    
        self.BOLD_RED = self.RED + self.BOLD
        self.BOLD_GREEN = self.GREEN + self.BOLD
        self.BOLD_ORANGE = self.ORANGE + self.BOLD
        self.BOLD_BLUE = self.BLUE + self.BOLD
        self.BOLD_LIGHT_GREEN = self.LIGHT_GREEN + self.BOLD
        self.BOLD_PURPLE = self.PURPLE + self.BOLD
        self.BOLD_CYAN = self.CYAN + self.BOLD
        self.BOLD_TURQUOISE = self.TURQUOISE + self.BOLD
        self.BOLD_WHITE = self.WHITE + self.BOLD
        self.BOLD_BLACK = self.BLACK + self.BOLD
        self.BOLD_YELLOW = self.YELLOW + self.BOLD
        self.BOLD_PINK = self.PINK + self.BOLD

    @staticmethod
    def rgb(red, green, blue):
        """
        This function converts RGB values to ANSI color codes.
        @param red: Red value of RGB 0-255.
        @type red: int.
        @param green: Green value of RGB 0-255.
        @type green: int.
        @param blue: Blue value of RGB 0-255.
        @type blue: int.
        @return: ANSI color code string.
        @rtype str.
        """
        return "\033[38;2;{};{};{}m".format(red, green, blue)

    def rand_color(self):
        """
        This function returns a random ANSI color code string.
        @return: Random ANSI color value string.
        @rtype str.
        """
        return self.rgb(
            random.choice(range(255)),
            random.choice(range(255)),
            random.choice(range(255)))

    def success_message(self, success, begins_with, ends_with):
        """
        This function create a success message.
        @param success: The specified success message.
        @type success: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: success message
        @rtype: str
        """
        return begins_with \
            + self.ENDC \
            + "[" \
            + self.BOLD_GREEN \
            + "!" \
            + self.ENDC \
            + "] " \
            + self.BOLD_GREEN \
            + success \
            + self.ENDC \
            + ends_with

    def print_success(self, success="SUCCESS!", begins_with="", ends_with=""):
        """
        This function prints a given success message.
        @param success: The specified success message.
        @type success: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: None.
        """
        print(self.success_message(success, begins_with, ends_with))

    def information_message(self, info, begins_with, ends_with):
        """
        This function create an information message.
        @param info: The specified information message.
        @type info: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: success message
        @rtype: str
        """
        return begins_with \
            + self.ENDC \
            + "[" \
            + self.LIGHT_BLUE \
            + "?" \
            + self.ENDC \
            + "] " \
            + self.LIGHT_BLUE \
            + info \
            + self.ENDC \
            + ends_with

    def print_information(self, info, begins_with="", ends_with=""):
        """
        This function prints a given information message.
        @param info: The specified information message.
        @type info: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: None.
        """
        print(self.information_message(info, begins_with, ends_with))

    def warning_message(self, warning, begins_with, ends_with):
        """
        This function create an warning message.
        @param warning: The specified warning message.
        @type warning: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: success message
        @rtype: str
        """
        return begins_with \
            + self.ENDC \
            + "[" \
            + self.BOLD_YELLOW \
            + "!" \
            + self.ENDC \
            + "] " \
            + self.BOLD_YELLOW \
            + warning \
            + self.ENDC \
            + ends_with

    def print_warning(self, warning="WARNING!", begins_with="", ends_with=""):
        """
        This function prints a specified warning message.
        @param warning: The specified warning.
        @type warning: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: None.
        """
        print(self.warning_message(warning, begins_with, ends_with))

    def error_message(self, error, begins_with, ends_with):
        """
        This function create an error message.
        @param error: The specified error message.
        @type error: str.
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: success message
        @rtype: str
        """
        return begins_with \
            + self.ENDC \
            + "[" \
            + self.BOLD_RED \
            + "!" \
            + self.ENDC \
            + "] " \
            + self.BOLD_RED \
            + error \
            + self.ENDC \
            + ends_with
    
    def print_error(self, error="ERROR!", begins_with="", ends_with=""):
        """
        This function prints a specified error message.
        @param error: The specified error.
        @type error: str
        @param begins_with: Optional string to start with.
        @type begins_with: str.
        @param ends_with: Optional string to end with.
        @type ends_with: str.
        @return: None.
        """
        print(self.error_message(error, begins_with, ends_with))

    def modify_string(self, input_str, parameters):
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
        
        @param input_str: The string to modify with the given parameters.
        @type input_str: str.
        @param parameters: The parameters to modify the string with, each parameter is a tuple of:
        >   (begin_index : int, stop_index : int, ansi_modification : str).
        @type parameters: list[tuple].
        @return: The modified string with the valid changes made to it, if for some reason there are some missing changes please read the description.
        @rtype str.
        """
        def validate_parameter(param, str_len):
            if len(param) != 3:
                return False
            type_bool: bool = all((type(param[0]) == int, type(param[1]) == int, type(param[2]) == str))
            size_bool: bool = all((param[0] >= 0, param[1] > 0, param[0] < param[1], param[1] <= str_len))
            return type_bool and size_bool
        # Get list of all valid parameters.
        valid_params = [param for param in parameters if validate_parameter(param, len(input_str))]
        if len(valid_params) == 0:
            return input_str
        
        # Get lists of all the needed indexes and sort them from last to first.
        endc_indexes = list(set([param[1] for param in valid_params]))
        endc_indexes.sort(reverse=True)
        mod_indexes = list(set([(param[0], param[2]) for param in valid_params]))
        mod_indexes.sort(key=lambda x: x[0], reverse=True)
        
        output_str = self.ENDC
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
                        ansi_to_add = self.ENDC
                        endci += 1
                    skip_endc = False
                else:
                    # Both need to be used and therefor we must put the endc first so the color will continue.
                    index = endc_index
                    ansi_to_add = self.ENDC + mod_index[1]
                    skip_endc = True
                    modi += 1
                    endci += 1
            elif mod_index is not None:
                index = mod_index[0]
                ansi_to_add = mod_index[1]
                modi += 1
            elif endc_index is not None:
                index = endc_index
                ansi_to_add = self.ENDC
                endci += 1
            
            # Append the modified text to the output string.
            output_str = ansi_to_add + input_str[index: prev_index] + output_str
            prev_index = index
        
        if index != 0:
            # If we did not reach the beginning of the string we need to add it.
            output_str = input_str[0: prev_index] + output_str
        
        return output_str


COLOR_MANAGER = Colors()  # Colors Object.
