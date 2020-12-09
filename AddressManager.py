#!/usr/bin/python3
import nmap
import Data
from colors import COLOR_MANAGER
import requests
from scapy.all import *
import subprocess

NUMBER_OF_PACKETS = 2
TTL = 2


def valid_ip(ip: str) -> bool:
    """
    Function checks if the IP is valid
    :param ip: the IP string
    :return: True - valid IP, False - invalid IP
    """

    def isIPv4(field: str) -> bool:
        """
        Function checks if a string is a number and between 0-255
        :param field: a field from the IP address
        :return: True - valid field, False - invalid field
        """
        return field.isnumeric() and 0 <= int(field) <= 255

    if ip.count(".") == 3 and all(isIPv4(field) for field in ip.split(".")):
        # If there are 4 fields in the IP and they all are in range 0-255
        return True
    return False


def valid_url(data: Data.Data):
    """
    Function checks if the url is valid
    :param data: the data object of the program
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
        data.url[len("http://") :].split("/")[0].split(":")
    )  # address = [ip, port]
    if len(address) == 1:
        # IP only, no port specified in URL
        if data.port is None:
            # Port wasn't specified under -p
            data.port = 80  # default port for http
        else:
            path = data.url[len("http://") + len(address[0]) :]
            data.url = f"http://{address[0]}:{data.port}{path}"
    elif len(address) == 2:
        # IP and port
        port = address[1]
        if port.isnumeric():
            # If port is a number
            port = int(port)
            if 65535 > port > 1:
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


def scan_ports(data: Data.Data):
    """
    Function scans the host on the specified port/s
    :param data: the data object of the program
    """
    nm = nmap.PortScanner()  # Instantiate nmap.PortScanner object
    nm.scan(hosts=data.ip, ports=str(data.port))  # Scan host, ports from 22 to 443

    if len(nm.all_hosts()) == 0:
        raise Exception(f"No hosts found on {data.ip}", "\t")

    host = nm[nm.all_hosts()[0]]  # Usually there is one host in the list, the one we want to check

    if type(data.port) is not int:
        # If the user used -P for all ports scan
        message = str()
        for proto in host.all_protocols():
            # For every protocol that the host is using
            ports = list(host[proto].keys())
            ports.sort()

            for port in ports:
                if host[proto][port]["name"] == "http":
                    # We are looking for http ports only
                    padding = " " * (5 - len(str(port)))
                    message += f"\t\tPort: {port}{padding} | State: {host[proto][port]['state']} " \
                               f"| Service: {host[proto][port]['product']}\n"
        if len(message) != 0:
            # If there are open http ports on the host
            message = (
                f"\t{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}List of the open http ports on your host:"
                f"{COLOR_MANAGER.ENDC}\n"
                + COLOR_MANAGER.YELLOW
                + message
                + f"\n\tPlease choose one of the ports above and try again (-p <port>).{COLOR_MANAGER.ENDC}\n"
            )
            print(message)
        else:
            # If there are no open http ports on the host
            raise Exception(
                "There are no open http ports on your host, please check the host.", "\t")
    else:
        # If the user used -p or used the default port 80
        print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
              f"Scanning port {data.port} for HTTP{COLOR_MANAGER.ENDC}")
        exists = False
        proto_list = host.all_protocols()
        for proto in proto_list:
            # Checking each protocol
            ports = list(host[proto].keys())  # Get all port numbers as a list.
            for port in ports:
                if (port == data.port
                        and host[proto][port]["name"] == "http"
                        and host[proto][port]["state"] == "open"):
                    # If the specified port is http and open
                    exists = True
                    break
        if exists:
            # If the specified port is good
            if data.url is None:
                # If the url field is empty
                data.url = f"http://{data.ip}:{data.port}/"
        else:
            # If the specified port is not good
            raise Exception(
                f"Port {data.port} isn't open on your host. please try another port or check your host.", "\t")


def ping(data: Data.Data):
    """
    Function checks if the host is up and in the local network
    :param data: the data object of the program
    """
    if data.ip == "127.0.0.1":
        return  # Our computer, there is no need to ping

    print(f"\t[{COLOR_MANAGER.YELLOW}%{COLOR_MANAGER.ENDC}]{COLOR_MANAGER.YELLOW} "
          f"Pinging {data.ip}{COLOR_MANAGER.ENDC}")

    result = subprocess.Popen(
        ["ping", "-r", "9", "-n", f"{NUMBER_OF_PACKETS}", data.ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result.wait()  # Wait for the thread to finish the ping
    out, err = result.communicate()  # out = The output of the ping
    if out:
        # If the ping made an output
        if "Access denied." in out.decode():
            # If the ping requires sudo privileges
            raise Exception("The process requires administrative privileges", "\t")
        elif "Lost = 0" in out.decode():
            # If the host is up
            if out.decode().count("->") > NUMBER_OF_PACKETS * TTL:
                # Every "->" represents a router that the ping going through
                # More than 2 routers are usually out of the local network
                raise Exception(f"The host {data.ip} is not in your local network", "\t")
        else:
            # If the host is down
            raise Exception(f"The host {data.ip} is down or too far", "\t")
    else:
        # Don't know when it can occur, just in case of unknown error
        raise Exception("Some error has occurred")


def set_target(data: Data.Data):
    """
    Function sets the address details in the Data object, checks ports, IP or URL.
    :param data: the data object of the program
    """
    print(f"\n{COLOR_MANAGER.HEADER}{COLOR_MANAGER.YELLOW}Achieving target:{COLOR_MANAGER.ENDC}")
    if data.url is not None:
        # If the user specified URL
        valid_url(data)
    elif not valid_ip(data.ip):
        # If the user didn't specified URL and the IP is invalid
        raise Exception(
            f"The IP {data.ip} is not in the right of format of xxx.xxx.xxx.xxx", "\t"
        )
    # At this point there has to be a valid IP
    # Ping the IP host, checks if the host is up and in our local network
    ping(data)
    # The IP is valid, now ports check
    scan_ports(data)
