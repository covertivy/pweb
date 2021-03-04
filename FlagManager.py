#!/usr/bin/python3
import argparse
from Classes import Data
from colors import COLOR_MANAGER


def char_arr_to_string(arr: list) -> str:
    """
    Function converts char array to string
    @param arr: Char array
    @return: String
    """
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def parse_args() -> argparse.Namespace:
    """
    Function gets command line arguments using argparse
    @return: Namespace of the arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        default=None,
        type=str,
        help="Enter the path to a JSON file which have a list of cookies or one cookie, "
             "every cookie must contain the keys: \"name\", \"value\" and \"domain\".",
        dest="cookies")
    parser.add_argument(
        "-i",
        type=str,
        help="Enter the ip of the host server. (Not necessary if argument <url> is specified)",
        dest="ip")
    parser.add_argument(
        "-V",
        "--verbose",
        action="store_false",
        help="Specify this flag when you don't want to print our cool logo.",
        dest="verbose")
    parser.add_argument(
        "-p",
        type=int,
        help="Specify a known port on which a web server is serving, if not specified, default port would be 80.\n "
        "You can use flag -P to force an all-port scan.",
        dest="port")
    parser.add_argument(
        "-P",
        "--all_ports",
        action="store_true",
        help="Specify this flag when port isn't known and you wish to scan all ports.",
        dest="all_ports")
    parser.add_argument(
        "-u",
        default=None,
        type=str,
        help="Instead of specifying an ip address you can specifically specify a url.",
        dest="url")
    parser.add_argument(
        "-n",
        default=None,
        type=int,
        help="Limit the amount of pages checked to a specific amount.",
        dest="number_of_pages")
    parser.add_argument(
        "-L",
        default=list(),
        type=list,
        nargs=2,
        help="Specify a username and password to be used in any login form on the website.",
        dest="login")
    parser.add_argument(
        "-o",
        default=None,
        type=str,
        help="Specify a file path in which the outputs will be stored (xml).",
        dest="output")
    parser.add_argument(
        "-R",
        "--recursive",
        action="store_true",
        help="recursive page scraper, will check all the reachable pages in the website.",
        dest="recursive",
        default=False)
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
        " whitelist must be a `.txt` file.",
        dest="whitelist")
    parser.add_argument(
        "-A",
        "--aggressive",
        action="store_true",
        help="some of the default plugins will mess up with the website data base and source code, "
        "this flag is your signing that you agree to have minimal damage in case of vulnerability.",
        dest="aggressive")
    args = parser.parse_args()
    return args


def get_final_args(args) -> Data:
    """
    Function gets the arguments into the Data object
    @param args: All the command line arguments.
    @return: The returned data object, will be processed furthermore in the Main Core.
    """
    output_obj = Data()

    # Set Username and Password
    if type(args.login) is not None:
        if len(args.login) == 2:
            output_obj.username = char_arr_to_string(args.login[0])
            output_obj.password = char_arr_to_string(args.login[1])

    # Set cookies
    output_obj.cookies = args.cookies

    # Set IP
    output_obj.ip = args.ip

    # Set URL
    output_obj.url = args.url
    if output_obj.url is not None and output_obj.url[-1] != "/":
        output_obj.url += "/"

    # Check if all ports flag is set.
    if args.all_ports:
        output_obj.port = 0
    else:
        output_obj.port = args.port

    # Set limit of pages.
    if args.number_of_pages and args.number_of_pages <= 0:
        # If the number is set and it is invalid
        COLOR_MANAGER.print_error("Invalid number of pages! Running with unlimited pages.")
        output_obj.max_pages = None
    else:
        # If the number wasn't specified or it was specified and is valid
        output_obj.max_pages = args.number_of_pages

    # Set output file path
    if args.output is not None:
        if args.output.endswith(".xml"):
            output_obj.output = args.output
        else:
            output_obj.output = args.output + ".xml"
    else:
        output_obj.output = args.output

    # Set blacklist file path
    if args.blacklist is not None:
        if args.blacklist.endswith(".txt"):
            output_obj.blacklist = args.blacklist
        else:
            output_obj.blacklist = args.blacklist + ".txt"
    else:
        output_obj.blacklist = args.blacklist

    # Set whitelist file path
    if args.whitelist is not None:
        if args.whitelist.endswith(".txt"):
            output_obj.whitelist = args.whitelist
        else:
            output_obj.whitelist = args.whitelist + ".txt"
    else:
        output_obj.whitelist = args.whitelist

    # Set recursive flag
    output_obj.recursive = args.recursive

    # Set verbose flag
    output_obj.verbose = args.verbose

    # Set agreement flag
    output_obj.aggressive = args.aggressive

    return output_obj
