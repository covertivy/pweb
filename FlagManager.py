#!/usr/bin/python3
import argparse
import Data
from colors import COLOR_MANAGER


def char_arr_to_string(arr: list) -> str:  # convert char array to string
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def parse_args():  # Get command line arguments using argsparse.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--ip",
        default="127.0.0.1",
        type=str,
        help="Enter the ip of the host server. (Not necessary if argument <url> is specified)",
    )
    parser.add_argument(
        "-p",
        "--port",
        default=80,
        type=int,
        help="Specify a known port on which a web server is serving, if not specified, default port would be 80.\n "
             "You can use flag -P to force an all-port scan.",
    )
    parser.add_argument(
        "-P",
        "--ALL_PORTS",
        action="store_true",
        help="Specify this flag when port isn't known and you wish to scan all ports.",
    )
    parser.add_argument(
        "-u",
        "--url",
        default="",
        type=str,
        help="Instead of specifying an ip address you can specifically specify a url.",
    )
    parser.add_argument(
        "-n",
        "--number_of_pages",
        default=None,
        type=int,
        help="Limit the amount of pages checked to a specific amount.",
    )
    parser.add_argument(
        "-L",
        "--login",
        default=list(),
        type=list,
        nargs=2,
        help="Specify a username and password to be used in any login form on the website.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        type=str,
        help="Specify a directory path in which the outputs will be stored.",
    )
    args = parser.parse_args()
    return args


def get_final_args(args) -> Data.Data:
    """
    Args:
        args: All the command line arguments.

    Returns:
        Data.Data: The returned data object, will be processed furthermore in the Main Core.
    """
    output_obj = Data.Data()

    if type(args.login) is not None:
        if len(args.login) == 2:
            output_obj.username = char_arr_to_string(args.login[0])
            output_obj.password = char_arr_to_string(args.login[1])
        # Username. Password.

    output_obj.ip = args.ip
    output_obj.url = args.url

    # Check if port is valid
    if args.port < 1 or args.port > 65535:
        COLOR_MANAGER.print_error("Invalid port number, using default port 80.")
        output_obj.port = 80
    else:
        output_obj.port = args.port

    if args.ALL_PORTS:
        output_obj.port = -1

    output_obj.max_pages = args.number_of_pages
    output_obj.folder = args.output

    return output_obj
