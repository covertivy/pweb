#!/usr/bin/python3
from Classes import Data
from colors import COLOR_MANAGER
import socket
import subprocess

MAXIMUM_PORT = 65535
NUMBER_OF_PACKETS = 2
TTL = 2


def valid_ip(ip: str) -> bool:
    """
    Function checks if the IP is valid
    @param ip: The IP string
    @return: True - valid IP, False - invalid IP
    """
    if ip.count(".") == 3 and \
            all(field.isnumeric() and 0 <= int(field) <= 255 for field in ip.split(".")):
        # If there are 4 fields in the IP and they all are in range 0-255
        return True
    return False


def valid_url(data: Data):
    """
    Function checks if the url is valid
    @param data: The data object of the program
    @return: None
    """
    if not str(data.url).lower().startswith("http://"):
        # If the URL does not start with "http://
        raise Exception("URL must start with 'http://'")

    try:
        name = str(data.url).replace("http://", "").split("/")[0]
        ip = socket.gethostbyname(name)
        data.url = str(data.url).replace(name, ip)
    except:
        pass

    address = (
        data.url[len("http://"):].split("/")[0].split(":")
    )  # address = [ip, port]
    if len(address) == 1:
        # IP only, no port specified in URL
        if data.port is None:
            # Port wasn't specified under -p
            data.port = 80  # default port for http
        else:
            path = data.url[len("http://") + len(address[0]):]
            data.url = f"http://{address[0]}:{data.port}{path}"
    elif len(address) == 2:
        # IP and port
        port = address[1]
        if port.isnumeric():
            # If port is a number
            port = int(port)
            if MAXIMUM_PORT > port > 0:
                # If port is in range
                data.port = port
            else:
                # Port out of range
                raise Exception(
                    f"Port in the URL is out of range ('{port}' is not between 0-255)", "\t"
                )
        else:
            # Port is not a number
            raise Exception(
                f"Port in the URL is not a number ('{port}' needs to be a number)", "\t"
            )

    data.ip = address[0]
    if not valid_ip(data.ip):
        # if the IP in the URL is invalid
        raise Exception(
            f"The IP {data.ip} is not in the right of format of xxx.xxx.xxx.xxx", "\t")


def scan_ports(data: Data):
    """
    Function scans the host on the specified port/s
    @param data: The data object of the program
    @return: None
    """
    if type(data.port) is not int:
        # If the user used -P for all ports scan
        ports_range = range(1, MAXIMUM_PORT + 1)
        plural = "s"
    else:
        # If the user used -p or used the default port 80
        ports_range = [data.port]
        plural = ""
    print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
          f"Scanning port{plural} {data.port} for HTTP{COLOR_MANAGER.ENDC}")
    if len(ports_range) > 1:
        # Scan all ports
        print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
              f"Will take about 6 minutes to finish...")
    http_ports = list()
    default_timeout = socket.getdefaulttimeout()  # Save it before changing it
    for port in ports_range:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0.005)
        try:
            if not sock.connect_ex((data.ip, port)):
                # If it is an open port
                if socket.getservbyport(port, 'tcp') == 'http':
                    # If it runs http protocol
                    http_ports.append(port)
        except Exception:
            continue
        sock.close()
    socket.setdefaulttimeout(default_timeout)  # Retrieving the default value
    if type(data.port) is not int:
        # If the user used -P for all ports scan
        results = str()
        for port in http_ports:
            padding = " " * (5 - len(str(port)))  # Padding the table rows
            results += f"\t- Port: {port}{padding} | State: open " \
                       f"| Proto: HTTP\n"
        if len(results) != 0:
            # If there are open http ports on the host
            message = (
                    f"\t{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}List of the open http ports on your host:"
                    f"{COLOR_MANAGER.ENDC}\n"
                    + COLOR_MANAGER.YELLOW
                    + results
                    + f"\n\tPlease choose one of the ports above and try again (-p <port>).{COLOR_MANAGER.ENDC}\n")
            print(message)
        else:
            # If there are no open http ports on the host
            raise Exception(
                "There are no open http ports on your host, please check the host or try again.", "\t")
    else:
        # If the user used -p or used the default port 80
        if len(http_ports):
            # If the specified port is good
            if data.url is None:
                # If the url field is empty
                data.url = f"http://{data.ip}:{data.port}/"
        else:
            # If the specified port is not good
            raise Exception(
                f"Port {data.port} isn't open on your host. please try another port or check your host.", "\t")


def ping(data: Data):
    """
    Function checks if the host is up and is in the local network
    @param data: The data object of the program
    @return: None
    """
    if data.ip == "127.0.0.1":
        return  # Our computer, there is no need to ping

    print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
          f"Pinging {data.ip}{COLOR_MANAGER.ENDC}")

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
            raise Exception(f"The host {data.ip} is down or too far.\n", "\t")
    else:
        # Don't know when it can occur, just in case of unknown error
        raise Exception("Some error has occurred.\n", "\t")


def set_target(data: Data):
    """
    Function sets the address details in the Data object, checks ports, IP or URL
    @param data: The data object of the program
    @return: None
    """
    print(f"\n{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}Achieving target:{COLOR_MANAGER.ENDC}")
    if data.url is not None:
        # If the user specified URL
        valid_url(data)
    elif not valid_ip(data.ip):
        # If the user didn't specified URL and the IP is invalid
        raise Exception(
            f"The IP {data.ip} is not in the right of format of xxx.xxx.xxx.xxx", "\t")
    # At this point there has to be a valid IP
    # Ping the IP host, checks if the host is up and in our local network
    ping(data)
    # The IP is valid, now ports check
    scan_ports(data)
