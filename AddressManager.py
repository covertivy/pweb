#!/usr/bin/python3
from Classes import Data
from colors import COLOR_MANAGER
import socket
import subprocess
from urllib.parse import urlparse
from threading import Lock, Thread


# ------- Consts ----------
MAXIMUM_PORT = 65356
NUMBER_OF_PACKETS = 2
TTL = 2
# -------------------------


def valid_address(data: Data):
    """
    Function checks if the URL, port and IP are valid
    @param data: The data object of the program
    @return: None
    """
    port = data.port
    url = data.url
    ip = data.ip
    scheme = "http"
    path = "/"
    query = ""
    if url:
        # URL is the most important
        if not url.startswith(scheme):
            # Does not start with http or https
            raise Exception("The URL is not in the right format of 'scheme://domain:port/path'.", "\t")
        parse = urlparse(url=data.url)  # Parsing the URL
        try:
            port = parse.port if parse.port else port  # Assigning the found port
            scheme = parse.scheme  # Must have a scheme (http or https)
            path = parse.path  # Must have a path (even "/" counts)
            query = "?" + parse.query if parse.query else query
        except Exception:
            print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
                  f"The port which was specified in the URL is invalid.{COLOR_MANAGER.ENDC}")
        try:
            ip = socket.gethostbyname(parse.hostname)
        except Exception:
            pass
    if ip:
        # Found IP in the URL or was already specified
        if ip.count(".") != 3 or \
                not all(field.isnumeric() and 0 <= int(field) <= 255 for field in ip.split(".")):
            # If the number of fields is not 4 or any of them are not in range of 0-255
            raise Exception(f"The IP is not in the right of format of xxx.xxx.xxx.xxx.", "\t")
    else:
        # The IP is not specified and the URL was not found
        raise Exception("No IP was specified or found through the URL.", "\t")
    if port:
        # A port was specified in the user's input
        if MAXIMUM_PORT <= port or port <= 0:
            # Port out of range
            raise Exception(
                f"Port is out of range ('{port}' is not between 0-255)", "\t")
    elif data.port == 0:
        # -P was specified
        port = 0
    else:
        # No port specified and -P was not specified
        print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
              f"Using default port 80.{COLOR_MANAGER.ENDC}")
        port = 80
    # Setting address into the data object
    data.url = f"{scheme}://{ip}:{port}{path}{query}"
    data.port = port
    data.ip = ip


def ping(data: Data):
    """
    Function checks if the host is up and is in the local network
    @param data: The data object of the program
    @return: None
    """
    if data.ip == "127.0.0.1":
        return  # Our computer, there is no need to ping

    print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
          f"Pinging {data.ip}.{COLOR_MANAGER.ENDC}")

    result = subprocess.Popen(
        ["ping", "-i", str(TTL), data.ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    result.wait()  # Wait for the thread to finish the ping
    out, err = result.communicate()  # out = The output of the ping
    if out:
        # If the ping made an output
        if "Access denied." in out.decode():
            # If the ping requires sudo privileges
            raise Exception("The process requires administrative privileges.\n", "\t")
        elif "TTL expired in transit" in out.decode():
            # If the host is down
            raise Exception(f"The host {data.ip} is down or too far, please try again.\n", "\t")
    else:
        # Don't know when it can occur, just in case of unknown error
        raise Exception("Some error has occurred.\n", "\t")


def scan_ports(data: Data):
    """
    Function scans the host on the specified port/s
    @param data: The data object of the program
    @return: None
    """
    open_ports = list()
    http_ports = list()
    mutex = Lock()
    ports_range = ""
    if data.port == 0:
        # If the user used -P for all ports scan
        plural = "s"
        ports_range = f"1-{MAXIMUM_PORT - 1}"  # Printing range
    else:
        # If the user used -p or used the default port 80
        plural = ""

    print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
          f"Scanning port{plural} {ports_range} for HTTP{COLOR_MANAGER.ENDC}\n")

    def scan_a_port(a_port: int):
        """
        Inner function scan a specific port
        @param a_port: The current port number
        @return: None
        """
        def print_line():
            """
            Prints a line in the table
            @return: None
            """
            print(COLOR_MANAGER.YELLOW + " " * 7 +
                  "+" + "-" * 13 +
                  "+" + "-" * 13 +
                  "+" + "-" * 24 + "+")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.02)  # Setting short default timeout
        try:
            sock.connect((data.ip, a_port))
            # If it is an open port it won't raise an exception
            try:
                proto = socket.getservbyport(a_port, 'tcp')
            except Exception:
                proto = "unknown"
            if plural:
                # In case of scanning all ports
                mutex.acquire()
                if not open_ports:
                    print(f"\t{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}"
                          f"List of the open ports on your host:{COLOR_MANAGER.ENDC}")
                    print_line()
                port_padding = " " * (5 - len(str(a_port)))  # Padding the table rows
                proto_padding = " " * (15 - len(proto))
                print(" " * 7 + f"{COLOR_MANAGER.YELLOW}| Port: {a_port}{port_padding}"
                                f" | State: open | Proto: {proto}{proto_padding} |")
                print_line()
                mutex.release()
            open_ports.append(a_port)
            if "http" in proto:
                http_ports.append(a_port)
        except Exception:
            pass
        sock.close()

    if plural:
        # If the user used -P for all ports scan
        threads = list()
        for port in range(1, MAXIMUM_PORT):
            # Setting the threads
            threads.append(Thread(target=scan_a_port, args=(port,)))
        for thread in threads:
            # Starting the threads
            thread.setDaemon(True)
            thread.start()
        for thread in threads:
            # Waiting for them to finish
            thread.join()
    else:
        scan_a_port(data.port)
    if plural:
        # If the user used -P for all ports scan
        if http_ports:
            # Found at least one open port
            print(f"\n\tPlease choose one of the ports above and try again (-p <port>).{COLOR_MANAGER.ENDC}\n")
        else:
            # If there are no open http ports on the host
            raise Exception(
                "There are no open http ports on your host, please check the host or try again.", "\t")
    else:
        # If the user used -p or used the default port 80
        if not http_ports:
            # If the specified port is not good
            raise Exception(
                f"Port {data.port} isn't open on your host. please try another port or check your host.", "\t")


def set_target(data: Data):
    """
    Function sets the address details in the Data object, checks ports, IP or URL
    @param data: The data object of the program
    @return: None
    """
    print(f"\n{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}Achieving target:{COLOR_MANAGER.ENDC}")
    valid_address(data)  # Validating the specified address
    # At this point there has to be a valid IP
    ping(data)  # Ping the IP host, checks if the host is up and in our local network
    scan_ports(data)  # The IP is valid, now ports check

