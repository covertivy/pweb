#!/usr/bin/python3
import argparse
import urllib
import colors
import sys

COLOR_MANAGER = colors.Colors()

def charr_to_string(arr:list) -> str:
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def validIPAddress(IP:str) -> bool:
    """
      :type IP: str
      :rtype: str
      """

    def isIPv4(s):
        try:
            return str(int(s)) == s and 0 <= int(s) <= 255
        except:
            return False

    if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
        return True
    return False


def valid_url(url:str) -> bool:
    token = urllib.parse.urlparse(url)
    min_attributes = ('scheme', 'netloc')  # protocol and domain
    if not all([getattr(token, attr) for attr in min_attributes]):
        return False
    else:
        return True


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
        default="",
        type=str,
        help="Specify a directory path in which the outputs will be stored.",
    )
    args = parser.parse_args()

    if args.url != "":
        IS_URL = True
    to_ret = dict()
    if type(args.login) != None:
        if len(args.login) == 2:
            creds = {
                "username": charr_to_string(args.login[0]),
                "password": charr_to_string(args.login[1]),
            }
            # Username. Password.
        else:
            creds = dict()
    else:
        creds = dict()

    if not validIPAddress(args.ip):
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid IP address, using default localhost."
            + COLOR_MANAGER.ENDC
        )
        args.ip = "127.0.0.1"
    
    if args.port < 1 or args.port > 65535:
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid port number, using default port 80."
            + COLOR_MANAGER.ENDC
        )
        args.port = 80

    if IS_URL and not valid_url(args.url):
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid url, using default port 80 on localhost."
            + COLOR_MANAGER.ENDC
        )
        args.url = ""
        args.ip = "127.0.0.1"
        args.port = 80
    else:
        # URL will be used.
        to_ret = {
            "ip": "",
            "port": args.port,
            "ALL_PORTS": args.ALL_PORTS,
            "IS_URL": True,
            "url": args.url,
            "num_of_pages": args.number_of_pages,
            "credentials": creds,
            "output": args.output,
        }
        return to_ret
        # IP will be used.
    to_ret = {
            "ip": args.ip,
            "port": args.port,
            "ALL_PORTS": args.ALL_PORTS,
            "IS_URL": False,
            "url": "",
            "num_of_pages": args.number_of_pages,
            "credentials": creds,
            "output": args.output,
        }
    return to_ret
