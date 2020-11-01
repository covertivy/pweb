#!/usr/bin/python3
import argparse
import colors
import Data


def charr_to_string(arr: list) -> str:
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def parse_args():
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
        help="Specify a known port on which a web server is serving, if not specified, default port would be 80.\n You can use flag -P to force an all-port scan.",
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
        default=str(),
        type=str,
        help="Specify a directory path in which the outputs will be stored.",
    )
    args = parser.parse_args()
    return args


def get_final_args(args) -> Data.Data:
    COLOR_MANAGER = colors.Colors()
    output_obj = Data.Data()

    if type(args.login) != None:
        if len(args.login) == 2:
                output_obj.username = charr_to_string(args.login[0])
                output_obj.password = charr_to_string(args.login[1])
            # Username. Password.
    
    output_obj.ip = args.ip
    output_obj.address = args.url

    if args.port < 1 or args.port > 65535:
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid port number, using default port 80."
            + COLOR_MANAGER.ENDC
        )
        output_obj.port = 80
    else:
        output_obj.port = args.port

    output_obj.all_ports = args.ALL_PORTS
    output_obj.max_pages = args.number_of_pages
    output_obj.folder = args.output
    
    return output_obj