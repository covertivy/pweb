import urllib.parse
import colors
import sys
import argparse
from parse_args import parse_args

args = parse_args()

COLOR_MANAGER = colors.Colors()


def charr_to_string(arr: list) -> str:
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def url_port(url: str, existing_port: int):
    try:
        token = urllib.parse.urlparse(url)
        port = token.port
    except ValueError as e:
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + f"[!] {e}, using port {existing_port}."
            + COLOR_MANAGER.ENDC
        )
        return existing_port
    if not port:
        return existing_port
    return port


def validIPAddress(IP: str) -> bool:
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


def valid_url(url: str) -> bool:
    token = urllib.parse.urlparse(url)

    min_attributes = ("scheme", "netloc")  # protocol and domain
    if not all([getattr(token, attr) for attr in min_attributes]):
        return False
    elif "." not in str(getattr(token, "netloc")):
        return False
    else:
        return True


def get_final_args(args):
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

    if not valid_url(args.url):
        if len(args.url) > 0:
            print(
                COLOR_MANAGER.BRIGHT_YELLOW
                + "[!] Invalid url, using ip instead."
                + COLOR_MANAGER.ENDC
            )
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
    else:
        # URL will be used.
        port = url_port(
            args.url, args.port
        )  # Get port from url, if invalid take args port.

        to_ret = {
            "ip": "",
            "port": port,
            "ALL_PORTS": args.ALL_PORTS,
            "IS_URL": True,
            "url": args.url,
            "num_of_pages": args.number_of_pages,
            "credentials": creds,
            "output": args.output,
        }
        return to_ret
