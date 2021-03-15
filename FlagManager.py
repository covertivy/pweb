#!/usr/bin/python3
import argparse
from Classes import Data
from colors import COLOR_MANAGER, startup
import datetime


# -------------------------------------------------- CONSTANTS --------------------------------------------------+
ONE_LINER = "R|"  # For lines which are longer from the default width.                                           |
MAX_LINE = 25  # For the 'epilog' variable.                                                                      |
PADDING = " " * 3  # For the examples line, instead ot '\t'.                                                     |
SEPARATOR = f"{PADDING}{COLOR_MANAGER.YELLOW}python{COLOR_MANAGER.LIGHT_GREEN} %(prog)s {COLOR_MANAGER.ENDC}"   #|
# ---------------------------------------------------------------------------------------------------------------+


def char_arr_to_string(arr: list):
    """
    This function converts a char array to a string.
    @param arr: A Character list.
    @type arr: list.
    @return: The string made from the char array.
    @rtype: str.
    """
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


class SmartFormatter(argparse.HelpFormatter):
    """
    A helper class that overrides the default functions of the argparse class.
    """
    def _format_usage(self, usage, actions, groups, prefix):
        # Function for the `description` variable.
        return startup() + COLOR_MANAGER.RED + argparse.HelpFormatter._format_usage(self, usage, actions, groups, f"\nUsage: ")

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


def examples():
    """
    This function creates a string of usage examples for the user.

    @return: The usage examples.
    @rtype: str.
    """
    return f"{COLOR_MANAGER.UNDERLINE}{COLOR_MANAGER.LIGHT_GREEN}examples of usage:{COLOR_MANAGER.ENDC}\n" \
           + SEPARATOR + \
           f"-i 192.168.56.102 -P\n" \
           + SEPARATOR + \
           f"-i 192.168.56.102 -p 8081 -R -A -V\n" \
           + SEPARATOR + \
           f"-u http://192.168.56.102:8081/ -n 20 -L admin admin\n" \
           + SEPARATOR + \
           f"-u http://192.168.56.102:8081/ -c cookies.json -o output.xml\n" \
           + SEPARATOR + \
           f"-u http://192.168.56.102/ -b blacklist.txt -w whitelist.txt\n"


def parse_args():
    """
    This function gets the command line arguments using the argparse module.

    @return: The namespace of the arguments.
    @rtype: argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description=f"{ONE_LINER}{COLOR_MANAGER.UNDERLINE}{COLOR_MANAGER.BLUE}This is a tool for "
                    f"pentesting web security "
                    f"flaws in sites and web servers.{COLOR_MANAGER.ENDC}",
        formatter_class=SmartFormatter,
        epilog=examples(),
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
        help="Specify a known port on which a web server is serving, if not specified, default port would be 80.\n "
             f"You can use flag -P to force an all-port scan.{COLOR_MANAGER.CYAN}",
        dest="port")
    parser.add_argument(
        "-c",
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
        help="Specify a file path in which the outputs will be stored (xml).",
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
        f" whitelist must be a `.txt` file.{COLOR_MANAGER.ENDC}",
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
        help=f"Specify this flag when you don't want to print our cool logo.{COLOR_MANAGER.GREEN}",
        dest="verbose")
    # Get the command line arguments.
    args = parser.parse_args()
    return args


def get_final_args(args: argparse.Namespace):
    """
    This function gets the arguments from the argparse namespace and inserts 
    them into a Data object which is returned to the main program.

    @param args: All the command line arguments.
    @type args: argparse.Namespace.
    @return: The returned data object, will be processed furthermore in the Main Core.
    @rtype: Data.
    """
    output_obj = Data()

    # Set the `Username and Password`.
    if type(args.login) is not None:
        if len(args.login) == 2:
            output_obj.username = char_arr_to_string(args.login[0])
            output_obj.password = char_arr_to_string(args.login[1])

    # Set the `cookies`.
    output_obj.cookies = args.cookies

    # Set the `Host IP` Address.
    output_obj.ip = args.ip

    # Set the `Website URL`.
    output_obj.url = args.url
    if output_obj.url is not None and output_obj.url[-1] != "/":
        output_obj.url += "/"

    # Check if `all_ports` flag is set.
    if args.all_ports:
        output_obj.port = 0
    else:
        # Set the `Host Port`.
        output_obj.port = args.port

    # Set the `maximum number of pages`.
    if args.number_of_pages and args.number_of_pages <= 0:
        # If the given number is invalid.
        COLOR_MANAGER.print_error("Invalid number of pages! Running with unlimited pages.")
        output_obj.max_pages = None
    else:
        # If the number wasn't specified or it was specified and is valid.
        output_obj.max_pages = args.number_of_pages

    # Set the `output file` name and path.
    if args.output is not None:
        if args.output.endswith(".xml"):
            output_obj.output = args.output
        else:
            output_obj.output = args.output + ".xml"
    else:
        output_obj.output = args.output

    # Set `blacklist` file path.
    if args.blacklist is not None:
        if args.blacklist.endswith(".txt"):
            output_obj.blacklist = args.blacklist
        else:
            output_obj.blacklist = args.blacklist + ".txt"
    else:
        output_obj.blacklist = args.blacklist

    # Set `whitelist` file path.
    if args.whitelist is not None:
        if args.whitelist.endswith(".txt"):
            output_obj.whitelist = args.whitelist
        else:
            output_obj.whitelist = args.whitelist + ".txt"
    else:
        output_obj.whitelist = args.whitelist

    # Set `recursive` flag.
    output_obj.recursive = args.recursive

    # Set `verbose` flag.
    output_obj.verbose = args.verbose
    if args.verbose:
        # Print startup logo and current time.
        print(startup())
        print(f"{COLOR_MANAGER.GREEN}Started on: {datetime.datetime.now()}{COLOR_MANAGER.ENDC}")

    # Set `aggressive` flag.
    output_obj.aggressive = args.aggressive

    return output_obj
