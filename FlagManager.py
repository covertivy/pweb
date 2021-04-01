#!/usr/bin/python3
import argparse
from Classes import Data, Manager
from colors import COLOR_MANAGER, startup
import datetime

# -------------------------------------------------- CONSTANTS --------------------------------------------------+
ONE_LINER = "R|"  # For lines which are longer from the default width.                                           |
MAX_LINE = 25  # For the 'epilog' variable.                                                                      |
PADDING = " " * 3  # For the examples line, instead ot '\t'.                                                     |
SEPARATOR = f"{PADDING}{COLOR_MANAGER.YELLOW}python{COLOR_MANAGER.LIGHT_GREEN} %(prog)s {COLOR_MANAGER.ENDC}"  # |
# ---------------------------------------------------------------------------------------------------------------+


class SmartFormatter(argparse.HelpFormatter):
    """
    A helper class that overrides the default functions of the argparse class.
    """
    def _format_usage(self, usage, actions, groups, prefix):
        # Function for the `description` variable.
        return startup() + COLOR_MANAGER.RED + \
               argparse.HelpFormatter._format_usage(self, usage, actions, groups, f"\nUsage: ")

    def _fill_text(self, text, width, indent):
        # Function for the `epilog` variable.
        if text.startswith(ONE_LINER):
            paragraphs = text[2:].splitlines()
            import textwrap
            rebroken = [textwrap.wrap(par, width + MAX_LINE) for par in paragraphs]
            rebrokenstr = []
            for tlinearr in rebroken:
                if len(tlinearr) == 0:
                    rebrokenstr.append("")
                else:
                    for tlinepiece in tlinearr:
                        rebrokenstr.append(tlinepiece)
            return '\n'.join(rebrokenstr)
        return argparse.RawDescriptionHelpFormatter._fill_text(self, text, width, indent)


class FlagManager(Manager):
    def __init__(self):
        pass

    @staticmethod
    def __char_arr_to_string(arr: list):
        """
        This function converts a char array to a string.
        @param arr: A Character list.
        @returns str: The string made from the char array.
        """
        to_ret = ""
        for item in arr:
            to_ret += str(item)
        return to_ret

    @staticmethod
    def __examples():
        """
        This function creates a string of usage examples for the user.
        @rtype: str
        @return: The usage examples.
        """
        return f"{COLOR_MANAGER.UNDERLINE}{COLOR_MANAGER.LIGHT_GREEN}examples of usage:{COLOR_MANAGER.ENDC}\n" \
               + SEPARATOR + \
               f"-i 192.168.56.102 -P\n" \
               + SEPARATOR + \
               f"-i 192.168.56.102 -p 8081 -R -A -V\n" \
               + SEPARATOR + \
               f"-u http://192.168.56.102:8081/ -n 20 -L admin admin\n" \
               + SEPARATOR + \
               f"-u http://192.168.56.102:8081/ -c cookies.json -o ./output_folder\n" \
               + SEPARATOR + \
               f"-u http://192.168.56.102/ -b blacklist.txt -w whitelist.txt\n"

    def __parse_args(self):
        """
        This function gets the command line arguments using the argparse module.
        @rtype: argparse.Namespace
        @return: The namespace of the arguments.
        """
        parser = argparse.ArgumentParser(
            description=f"{ONE_LINER}{COLOR_MANAGER.UNDERLINE}{COLOR_MANAGER.BLUE}This is a tool for "
                        f"pentesting web security "
                        f"flaws in sites and web servers.{COLOR_MANAGER.ENDC}",
            formatter_class=SmartFormatter,
            epilog=self.__examples(),
            add_help=False)
        # Change the title.
        parser._optionals.title = f'{COLOR_MANAGER.UNDERLINE}Optional arguments{COLOR_MANAGER.ENDC}'
        # Add arguments.
        parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                            help=f'Show this help message and exit.{COLOR_MANAGER.YELLOW}')
        parser.add_argument(
            "-i",
            type=str,
            help="Enter the ip of the host server. (Not necessary if argument <url> is specified)",
            dest="ip")
        parser.add_argument(
            "-u",
            default=None,
            type=str,
            help=f"Instead of specifying an ip address you can specifically specify a url.{COLOR_MANAGER.ORANGE}",
            dest="url")
        parser.add_argument(
            "-p",
            type=int,
            help="Specify a known port on which a web server is serving,"
                 " if not specified, default port would be 80.\n "
                 f"You can use flag -P to force an all-port scan.{COLOR_MANAGER.CYAN}",
            dest="port")
        parser.add_argument(
            "-c",
            "--cookies",
            default=None,
            type=str,
            help="Enter the path to a JSON file which have a list of cookies or one cookie, "
                 "every cookie must contain the keys: \"name\" and \"value\".",
            dest="cookies")
        parser.add_argument(
            "-L",
            default=list(),
            type=list,
            nargs=2,
            help=f"Specify a username and password to be used in any login form on the website.",
            dest="login")
        parser.add_argument(
            "-n",
            default=None,
            type=int,
            help=f"Limit the amount of pages checked to a specific amount.{COLOR_MANAGER.PINK}",
            dest="number_of_pages")
        parser.add_argument(
            "-o",
            default=None,
            type=str,
            help="Specify a folder path in which the outputs will be stored as text files.",
            dest="output")
        parser.add_argument(
            "-b",
            "--blacklist",
            type=str,
            default=None,
            help="Specify a blacklist of words that may be found in a page's URL, "
                 " if the word is in the page url, the page is blocked. blacklist must be a `.txt` file.",
            dest="blacklist")
        parser.add_argument(
            "-w",
            "--whitelist",
            type=str,
            default=None,
            help="Specify a whitelist of words that may be found in a page's URL, "
                 " if the word is in the page url, the page is will be saved, otherwise we ignore the page,"
                 f" whitelist must be a `.txt` file.{COLOR_MANAGER.GREEN}",
            dest="whitelist")
        parser.add_argument(
            "-P",
            "--all_ports",
            action="store_true",
            help=f"Specify this flag when port isn't known and you wish to scan all ports.",
            dest="all_ports")
        parser.add_argument(
            "-R",
            "--recursive",
            action="store_true",
            help="Recursive page scraper, will check all the reachable pages in the website.",
            dest="recursive",
            default=False)
        parser.add_argument(
            "-A",
            "--aggressive",
            action="store_true",
            help="some of the default plugins will mess up with the website data base and source code, "
                 "this flag is your signing that you agree to have minimal damage in case of vulnerability.",
            dest="aggressive")
        parser.add_argument(
            "-V",
            "--verbose",
            action="store_false",
            help=f"Specify this flag when you don't want to print our cool logo.{COLOR_MANAGER.ENDC}",
            dest="verbose")
        # Get the command line arguments.
        args = parser.parse_args()
        return args

    def __get_final_args(self, data, args):
        """
        This function gets the arguments from the argparse namespace and inserts
        them into a Data object which is returned to the main program.
        @type data: Classes.Data
        @param data: The data object of the program
        @param args: All the command line arguments.
        @type args: argparse.Namespace
        @rtype: Data
        @return: The returned data object, will be processed furthermore in the Main Core.
        """
        # Set the `Username and Password`.
        if type(args.login) is not None:
            if len(args.login) == 2:
                data.username = self.__char_arr_to_string(args.login[0])
                data.password = self.__char_arr_to_string(args.login[1])

        # Set the `cookies`.
        data.cookies = args.cookies

        # Set the `Host IP` Address.
        data.ip = args.ip

        # Set the `Website URL`.
        data.url = args.url

        # Check if `all_ports` flag is set.
        if args.all_ports:
            data.port = 0
        else:
            # Set the `Host Port`.
            data.port = args.port

        # Set the `maximum number of pages`.
        if args.number_of_pages and args.number_of_pages <= 0:
            # If the given number is invalid.
            COLOR_MANAGER.print_error("Invalid number of pages! Running with unlimited pages.")
            data.max_pages = None
        else:
            # If the number wasn't specified or it was specified and is valid.
            data.max_pages = args.number_of_pages

        # Set the `output file` name and path.
        data.output = args.output

        # Set `blacklist` file path.
        if args.blacklist is not None:
            if args.blacklist.endswith(".txt"):
                data.blacklist = args.blacklist
            else:
                data.blacklist = args.blacklist + ".txt"
        else:
            data.blacklist = args.blacklist

        # Set `whitelist` file path.
        if args.whitelist is not None:
            if args.whitelist.endswith(".txt"):
                data.whitelist = args.whitelist
            else:
                data.whitelist = args.whitelist + ".txt"
        else:
            data.whitelist = args.whitelist

        # Set `recursive` flag.
        data.recursive = args.recursive

        # Set `verbose` flag.
        data.verbose = args.verbose
        if args.verbose:
            # Print startup logo and current time.
            print(startup())
            print(f"{COLOR_MANAGER.GREEN}Started on: {datetime.datetime.now()}{COLOR_MANAGER.ENDC}")

        # Set `aggressive` flag.
        data.aggressive = args.aggressive

    def logic(self, data):
        """
        Function gets the user's arguments and inserts them into the data instance.
        @type data: Classes.Data
        @param data: The data object of the program
        @return: None
        """
        args = self.__parse_args()
        self.__get_final_args(data, args)
