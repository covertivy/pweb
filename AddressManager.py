#!/usr/bin/python3
import nmap
import Data
from colors import COLOR_MANAGER
import requests
from scapy.all import *
import subprocess


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

    if ip.count(".") == 3 \
            and all(isIPv4(field) for field in ip.split(".")):
        # if there are 4 fields in the IP and they all are in range 0-255
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
        name = str(data.url).replace('http://', '').split("/")[0]
        ip = socket.gethostbyname(name)
        data.ip = ip
        data.port = 80
        return
    except:
        pass

    address = data.url[7:].split('/')[0].split(":")  # address = [ip, port]
    if len(address) == 1:
        # ip only, no port specified
        data.port = 80  # default port for http
    elif len(address) == 2:
        # ip and port
        port = address[1]
        if port.isnumeric():
            # if port is a number
            port = int(port)
            if 65535 > port > 1:
                # if port is in range
                data.port = port
            else:
                # port out of range
                raise Exception(f"Port in the URL is out of range ('{port}' is not between 0-255)")
        else:
            # port is not a number
            raise Exception(f"Port in the URL is not a number ('{port}' needs to be a number)")

    data.ip = address[0]

    if not valid_ip(data.ip):
        # if the IP in the URL is invalid
        raise Exception(f"The IP {data.ip} is not in the right of format of xxx.xxx.xxx.xxx")

    code = requests.get(data.url).status_code
    if code != 200:
        # if the URL is not responding
        raise Exception(f"The URL does not responds and returns status code: {code}")


def scan_ports(data: Data.Data):
    """
    Function scans the host on the specified port/s
    :param data: the data object of the program
    """
    nm = nmap.PortScanner()  # instantiate nmap.PortScanner object
    nm.scan(hosts=data.ip, ports=str(data.port))  # scan host, ports from 22 to 443

    if len(nm.all_hosts()) == 0:
        raise Exception(f"No hosts found on {data.ip}")

    host = nm[nm.all_hosts()[0]]  # usually there is one host in the list, the one we want to check

    if type(data.port) is not int:
        # if the user used -P for all ports scan
        message = str()
        for proto in host.all_protocols():
            # for every protocol that the host is using
            ports = list(host[proto].keys())
            ports.sort()

            for port in ports:
                if host[proto][port]['name'] == "http":
                    # we are looking for http ports only
                    message += f"\tPort: {port} | State: {host[proto][port]['state']} " \
                               f"| Service: {host[proto][port]['product']}\n"
        if len(message) != 0:
            # if there are open http ports on the host
            message = COLOR_MANAGER.UNDERLINE + \
                      "List of the open http ports on your host:\n\n" \
                      + COLOR_MANAGER.ENDC + COLOR_MANAGER.CYAN + message + COLOR_MANAGER.ENDC + \
                      "\nPlease choose one of the ports above and try again (-p <port>).\n"
            print(message)
        else:
            # if there are no open http ports on the host
            raise Exception("There are no open http ports on your host, please check the host.")
    else:
        # if the user used -p or used the default port 80
        exists = False
        proto_list = host.all_protocols()
        for proto in proto_list:
            # checking each protocol
            ports = list(host[proto].keys())  # Get all port numbers as a list.
            for port in ports:
                if port == data.port and host[proto][port]['name'] == 'http' \
                        and host[proto][port]['state'] == "open":
                    # if the specified port is http and open
                    exists = True
                    break
        if exists:
            # if the specified port is good
            if data.url is None:
                # if the url field is empty
                data.url = f"http://{data.ip}:{data.port}/"
        else:
            # if the specified port is not good
            raise Exception(f"port {data.port} isn't open on your host. please try another port or check your host.")


def ping(data: Data.Data):
    """
    Function checks if the host is up and in the local network
    :param data: the data object of the program
    """
    if data.ip == "127.0.0.1":
        return  # Our computer, there is no need to ping
    result = subprocess.Popen(["ping", "-r", "9", "-n", "4", data.ip],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.wait()  # Wait for the thread to finish the ping
    out, err = result.communicate()  # out = The output of the ping
    if out:
        # If the ping made an output
        if "Access denied." in out.decode():
            # If the ping requires sudo privileges
            raise Exception("The process requires administrative privileges")
        elif "Lost = 0" in out.decode():
            # If the host is up
            if out.decode().count("->") > 2:
                # Every "->" represents a router that the ping going through
                # More than 2 routers are usually out of the local network
                raise Exception(f"The host {data.ip} is not in your local network")
        else:
            # If the host is down
            raise Exception(f"The host {data.ip} is down or too far")
    else:
        # Don't know when it can occur, just in case of unknown error
        raise Exception("Some error has occurred")


def set_target(data: Data.Data):
    """
    Function sets the address details in the Data object, checks ports, IP or URL.
    :param data: the data object of the program
    """
    if data.url is not None:
        # If the user specified URL
        valid_url(data)
    elif not valid_ip(data.ip):
        # If the user didn't specified URL and the IP is invalid
        raise Exception(f"The IP {data.ip} is not in the right of format of xxx.xxx.xxx.xxx")
    # At this point there has to be a valid IP
    # Ping the IP host, checks if the host is up and in our local network
    ping(data)
    # The IP is valid, now ports check
    scan_ports(data)
