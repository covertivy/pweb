#!/usr/bin/python3
import argparse


def parse_args() -> dict:
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
